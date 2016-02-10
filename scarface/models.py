import logging
from abc import abstractmethod, abstractproperty
import json
from boto.exception import BotoServerError
import re
from django.db import models
from scarface.platform_strategy import get_strategies
from scarface.utils import DefaultConnection, PushLogger
from scarface.exceptions import SNSNotCreatedException, PlatformNotSupported, \
    SNSException, NotRegisteredException


logger = logging.getLogger('django_scarface')


class SNSCRUDMixin(object):

    @abstractproperty
    def resource_name(self):
        pass

    @property
    def response_key(self):
        '''
        Used for extracting the arn key from a response.
        '''
        return u'Create{0}Response'.format(self.resource_name)

    @property
    def result_key(self):
        '''
        Used for extracting the arn key from a response.
        '''
        return u'Create{0}Result'.format(self.resource_name)

    @property
    def arn_key(self):
        '''
        Used for extracting the arn key from a response.
        '''
        return u'{0}Arn'.format(self.resource_name)

    @property
    def is_registered(self):
        '''
        Returns whether the the instance is registered
        to SNS or not
        '''
        return self.arn and len(self.arn) > 0

    def is_registered_or_register(self):
        if not self.is_registered:
            return self.register()
        return True

    def set_arn_from_response(self, response_dict):
        """
        Extracts the arn key from a boto response dict.
        :type response_dict: dict
        :param response_dict:
        :rtype boolean:
        :return :
        """
        success = False
        try:
            self.arn = response_dict[self.response_key][self.result_key][
                self.arn_key]
            success = True
        except KeyError:
            pass
        return success

    @abstractmethod
    def register(self, connection=None):
        """
        Registers the instance to SNS.
        :param connection:
        :rtype boolean:
        :return: if create was successful
        """
        pass


class Application(models.Model):
    '''
    Main access point for the scarface library. Is used
    to manage the different platforms.
    '''
    name = models.CharField(
        max_length=255,
        unique=True
    )

    def __str__(self):
        return self.name

    def get_device(self, device_id):
        '''
        Returns a device by its device_id.
        '''
        return self.devices.get(udid=device_id)

    def get_topic(self, name):
        '''
        Returns a topic by its name.
        '''
        return self.topics.get(name=name)

    def get_or_create_topic(self, name):
        '''
        Returns a topic by its name. If the topic is
        not yet registered with this application the
        topic is created.
        :return: Topic, created
        :exception SNSException
        '''
        try:
            return self.topics.get(name=name), False
        except Topic.DoesNotExist:
            topic = Topic.objects.create(
                application=self,
                name=name
            )
            topic.register()
            topic.save()
            return topic, True

    def get_platform(self, platform_type):

        try:
            return self.platforms.get(platform=platform_type)
        except Platform.DoesNotExist:
            raise PlatformNotSupported


class Device(SNSCRUDMixin, models.Model):
    '''
    Device class for registering a end point to
    SNS.
    '''

    device_id = models.CharField(
        max_length=255,
    )

    platform = models.ForeignKey(
        to='Platform',
        related_name='devices'
    )

    arn = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    push_token = models.CharField(
        max_length=512,
    )

    topics = models.ManyToManyField(
        to='Topic',
        through='Subscription'
    )

    class Meta:
        unique_together = (('device_id', 'platform'))

    @property
    def resource_name(self):
        return 'PlatformEndpoint'

    @property
    def arn_key(self):
        return "EndpointArn"

    @DefaultConnection
    def register(self, custom_user_data='', connection=None):
        '''
        :exception SNSException
        '''
        self.platform.is_registered_or_register()
        response = connection.create_platform_endpoint(
            self.platform.arn,
            self.push_token,
            custom_user_data=custom_user_data
        )
        success = self.set_arn_from_response(response)
        if not success:
            raise SNSException(
                'Failed to register Device.({0})'.format(success)
            )
        self.save()
        return success

    @DefaultConnection
    def register_or_update(self, new_token=None, custom_user_data=u"",
                           connection=None):
        '''
        Registers the device to SNS. If the device was
        previously registered the registration is updated.
        :return: True if the registration/update was successful
        '''
        if self.is_registered:
            result = self.update(new_token, custom_user_data, connection)
        else:
            try:
                result = self.register(custom_user_data, connection)
            # Heavily inspired by http://stackoverflow.com/a/28316993/270265
            except BotoServerError as err:
                result_re = re.compile(r'Endpoint(.*)already', re.IGNORECASE)
                result = result_re.search(err.message)
                if result:
                    arn = result.group(0).replace('Endpoint ', '').replace(
                        ' already', '')
                    self.arn = arn
                    self.update(new_token, custom_user_data, connection)
                else:
                    sns_exc = SNSNotCreatedException(err)
                    sns_exc.message = err.message
                    raise sns_exc

        return result

    @DefaultConnection
    def deregister(self, connection=None, save=True):
        """
        Dergisters the device from SNS.
        :type connection: SNSConnection
        :param connection: the connection which should be used.
        if the argument isn't set there will be created a default connection
        :param save: weather the device should be saved, after the device has
        been deregsitered.
        :return:
        """
        if not self.is_registered:
            raise NotRegisteredException()
        success = connection.delete_endpoint(self.arn)
        if not success:
            SNSException(
                'Failed to deregister device.({0})'.format(success)
            )
        self.arn = None
        if save: self.save()
        return success

    @DefaultConnection
    def send_message(self, message, connection=None):
        if not self.is_registered:
            raise NotRegisteredException
        return connection.publish(message=message, target_arn=self.arn)

    @PushLogger
    @DefaultConnection
    def send(self, push_message, connection=None):
        """
        :type connection: SNSConnection
        :param connection: the connection which should be used.
        if the argument isn't set there will be created a default connection
        :return:
        """
        if not self.is_registered:
            raise NotRegisteredException
        push_message = self.platform.format_payload(push_message)
        json_string = json.dumps(push_message)
        return connection.publish(
            message=json_string,
            target_arn=self.arn,
            message_structure="json"
        )

    @DefaultConnection
    def update(self, new_token=None, custom_user_data=u"", connection=None):
        """
        :type connection: SNSConnection
        :param connection: the connection which should be used.
        if the argument isn't set there will be created a default connection
        :return:
        """
        if not self.is_registered:
            raise NotRegisteredException

        new_token = new_token if new_token else self.push_token
        attributes = {"Enabled": True, "Token": new_token}
        if custom_user_data:
            attributes["CustomUserData"] = custom_user_data
        answer = connection.set_endpoint_attributes(self.arn, attributes)
        self.is_enabled = True
        self.push_token = new_token
        return answer

    def sign(self, push_message):
        push_message.receiver_arn = self.arn
        push_message.message_type = PushMessage.MESSAGE_TYPE_TOPIC


class Platform(SNSCRUDMixin, models.Model):
    platform = models.CharField(
        max_length=255,
    )

    arn = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    application = models.ForeignKey(
        to=Application,
        related_name='platforms'
    )

    credential = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    principal = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    def __str__(self):
        return "{0} ({1})".format(self.platform, self.application)

    class Meta:
        unique_together = ('application', 'platform')

    @property
    def app_name(self):
        return self.application.name

    @property
    def strategy(self):
        strategies = get_strategies()
        if self.platform in strategies.keys():
            return strategies[self.platform](self)
        else:
            raise PlatformNotSupported

    @property
    def name(self):
        return u"_".join([self.app_name, self.platform]).lower()

    @property
    def resource_name(self):
        return 'PlatformApplication'

    @property
    def attributes(self):
        return {
            "PlatformCredential": self.credential,
            "PlatformPrincipal": self.principal
        }

    @DefaultConnection
    def register(self, connection=None):
        """
        Adds an app to SNS. Apps are per platform. The name of a
        sns application is app_platform.

        :type connection: SNSConnection
        :param connection: the connection which should be used.
        if the argument isn't set there will be created a default connection
        :rtype bool:
        :return:
        """

        response = connection.create_platform_application(
            self.name,
            self.platform,
            self.attributes
        )
        if not response:
            raise SNSException(
                'Failed to register Platform.{0}'.format(response)
            )
        return self.set_arn_from_response(response)

    @DefaultConnection
    def deregister(self, connection=None, save=True):
        """
        :type connection: SNSConnection
        :param connection: the connection which should be used.
        if the argument isn't set there will be created a default connection
        :return:
        """
        if not self.is_registered:
            raise NotRegisteredException

        success = connection.delete_platform_application(self.arn)
        if not success:
            SNSException(
                'Failded to deregister Platform.({0})'.format(success)
            )
        self.arn = None
        if save: self.save()
        return success

    @DefaultConnection
    def all_devices(self, connection=None):
        """
        Returns all devices which are registred with this
        platform.

        :param connection:
        :return: List of Devices associated with this platform
        """
        endpoint_arns = list()

        def get_next(nexttoken):
            response = connection.list_endpoints_by_platform_application(
                platform_application_arn=self.arn,
                next_token=nexttoken)
            result = response[u'ListEndpointsByPlatformApplicationResponse'][
                u'ListEndpointsByPlatformApplicationResult']
            endpoints = result[u'Endpoints']
            for endpoint in endpoints:
                endpoint_arns.append(
                    endpoint['EndpointArn']
                )

            return result[u'NextToken']

        next_token = get_next(None)

        while next_token:
            next_token = get_next(next_token)

        devices_list = list(Device.objects.filter(arn__in=endpoint_arns))

        return devices_list

    def format_payload(self, data):
        return self.strategy.format_payload(data)


class Topic(SNSCRUDMixin, models.Model):
    name = models.CharField(
        max_length=64
    )
    application = models.ForeignKey(
        to=Application,
        related_name='topics'
    )
    arn = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    devices = models.ManyToManyField(
        to=Device,
        through='Subscription'
    )

    class Meta:
        unique_together = (('name', 'application'))

    @property
    def resource_name(self):
        return 'Topic'

    @property
    def full_name(self):
        return '_'.join([self.application.name, self.name])

    @DefaultConnection
    def register(self, connection=None):

        response = connection.create_topic(self.full_name)
        if not response:
            raise SNSException(
                'Failed to register Topic. ({0})'.format(response)
            )
        self.set_arn_from_response(response)
        self.save()

    @DefaultConnection
    def deregister(self, connection=None, save=True):
        if not self.is_registered:
            raise NotRegisteredException
        success = connection.delete_topic(self.arn)
        if not success:
            raise SNSException(
                'Failed to deregister Topic. ({0})'.format(success)
            )

        self.arn = None
        if save: self.save()

        return success

    @DefaultConnection
    def register_device(self, device, connection=None):
        """
        :type device: Device
        :param device:
        :type connection: SNSConnection
        :param connection: the connection which should be used.
        if the argument isn't set there will be created a default connection
        :rtype bool:
        :return:
        """
        self.is_registered_or_register()
        device.is_registered_or_register()
        subscription, created = Subscription.objects.get_or_create(
            device=device,
            topic=self,
        )
        success = subscription.register(connection)
        return success

    @DefaultConnection
    def deregister_device(self, device, connection=None):
        if not device.is_registered:
            raise NotRegisteredException
        try:
            subscription = Subscription.objects.get(
                device=device,
                topic=self
            )
            subscription.deregister(connection)
            subscription.delete()
        except Subscription.DoesNotExist:
            logger.warn("Device is not registerd with topic.")
            return False
        return True

    @DefaultConnection
    def all_subscriptions(self, connection=None):
        subscriptions_list = list()

        def get_next(nexttoken):
            response = connection.get_all_subscriptions_by_topic(
                topic=self.arn, next_token=nexttoken)
            result = response["ListSubscriptionsByTopicResponse"][
                "ListSubscriptionsByTopicResult"]
            subs = result[u'Subscriptions']
            subscriptions_list.extend(subs)
            return result[u'NextToken']

        next_token = get_next(None)

        while next_token:
            next_token = get_next(next_token)

        return subscriptions_list

    def sign(self, push_message):
        push_message.receiver_arn = self.arn
        push_message.message_type = PushMessage.MESSAGE_TYPE_TOPIC

    @PushLogger
    @DefaultConnection
    def send(self, push_message, connection=None):
        """

        :type push_message: PushMessage
        :param push_message:
        :type platforms:list
        :param platforms:
        :return:
        """
        payload = dict()
        for platform in self.application.platforms.all():
            payload.update(platform.format_payload(push_message))
        payload["default"] = push_message.message
        json_string = json.dumps(payload)
        return connection.publish(
            message=json_string,
            topic=self.arn,
            message_structure="json"
        )


class PushMessage(models.Model):
    MESSAGE_TYPE_DEFAULT = 0
    MESSAGE_TYPE_TOPIC = 1
    sound = models.TextField(blank=True, null=True)
    message = models.TextField(default='', null=True)
    has_new_content = models.BooleanField(default=False)
    context_id = models.TextField(default='none', null=True)
    context = models.TextField(default='default', null=True)
    badge_count = models.SmallIntegerField(default=0)
    extra_payload = models.TextField(blank=True, null=True)
    receiver_arn = models.TextField(blank=True, null=True)
    message_type = models.PositiveSmallIntegerField(default=0)

    def as_dict(self):
        d = {
            'message': self.message,
            'context': self.context,
            'context_id': self.context_id,
            'badge_count': self.badge_count,
            'sound': self.sound,
            'has_new_content': self.has_new_content
        }
        if self.extra_payload:
            d.update(self.extra_payload)
        return d


class Subscription(SNSCRUDMixin, models.Model):
    topic = models.ForeignKey(
        to=Topic,
        on_delete=models.CASCADE
    )

    device = models.ForeignKey(
        to=Device,
        on_delete=models.CASCADE
    )

    arn = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    class Meta:
        unique_together = (('topic', 'device'))

    @property
    def response_key(self):
        return u'SubscribeResponse'

    @property
    def result_key(self):
        return u'SubscribeResult'

    @property
    def arn_key(self):
        return u'SubscriptionArn'

    @DefaultConnection
    def register(self, connection=None):
        self.device.is_registered_or_register()
        self.topic.is_registered_or_register()
        success = connection.subscribe(
            topic=self.topic.arn,
            endpoint=self.device.arn,
            protocol="application"
        )
        if not success:
            raise SNSException(
                'Failed to subscribe device to topic.({0})'.format(success)
            )
        self.set_arn_from_response(success)
        self.save()

    @DefaultConnection
    def deregister(self, connection=None, save=True):
        if not self.is_registered:
            raise NotRegisteredException
        success = connection.unsubscribe(self.arn)
        if not success:
            raise SNSException(
                'Failed to unsubscribe Device from Topic.({0})'.format(success)
            )
        self.arn = None
        if save: self.save()
        return success
