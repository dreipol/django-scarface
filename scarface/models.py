import logging
from abc import ABCMeta, abstractmethod
import json
from boto.exception import BotoServerError
import re
from django.db import models
from .utils import DefaultConnection, PushLogger
from scarface.exceptions import SNSNotCreatedException, PlatformNotSupported

logger = logging.getLogger('django_scarface')

AVAILABLE_PLATFORMS = {
    # 'ADM': 'Amazon Device Messaging (ADM)',
    'APNS': 'Apple Push Notification Service (APNS)',
    'APNS_SANDBOX': 'Apple Push Notification Service Sandbox (APNS_SANDBOX)',
    'GCM': 'Google Cloud Messaging (GCM)',
}

IOS = 1
ANDROID = 2
OS = {
    IOS: 'iOS',
    ANDROID: 'Android',
}


class SNSCRUDMixin(object):

    @property
    def resource_name(self):
        return self.name

    @property
    def response_key(self):
        return u'Create{0}Response'.format(self.resource_name)

    @property
    def result_key(self):
        return u'Create{0}Result'.format(self.resource_name)

    @property
    def arn_key(self):
        return u'{0}Arn'.format(self.resource_name)

    @property
    def is_registered(self):
        return self.arn is not None

    def set_arn_from_response(self, response_dict):
        """
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

        :param connection:
        :rtype boolean:
        :return: if create was successful
        """
        pass


class Application(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True
    )

    def __str__(self):
        return self.name

    def get_device(self, device_id):
        return self.devices.filter(udid=device_id)

    def get_topic(self, name):
        return self.topics.get(name=name)

    def get_or_create_topic(self, name):
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

    def platform_for_device(self, device):
        platform = None
        if device.os is IOS:
            platform = self.platforms.filter(platform__in=[
                'APNS',
                'APNS_SANDBOX',
            ]).first()
        elif device.os is ANDROID:
            platform = self.platforms.filter(platform__in=['GCM']).first()

        if not platform:
            raise PlatformNotSupported()
        return platform


class Device(SNSCRUDMixin, models.Model):
    device_id = models.CharField(
        max_length=255,
    )

    application = models.ForeignKey(
        to=Application,
        related_name='devices'
    )

    arn = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    push_token = models.CharField(
        max_length=255,
    )

    os = models.SmallIntegerField(
        choices=OS.items()
    )

    topics = models.ManyToManyField(
        to='Topic',
        through='Subscription'
    )

    class Meta:
        unique_together = (('device_id', 'application'))

    @property
    def resource_name(self):
        return 'PlatformEndpoint'

    @property
    def arn_key(self):
        return "EndpointArn"

    @property
    def platform(self):
        if not hasattr(self, '_platform'):
            self._platform = self.application.platform_for_device(self)
        return self._platform

    def delete(self, using=None, connection=None):
        if not self.deregister(connection):
            logger.warn("Could not unregister device on delete.")
        super().delete(using)

    @DefaultConnection
    def register(self, custom_user_data='', connection=None):
        if not self.platform.is_registered:
            success = self.platform.register(connection)
            if not success:
                return success
        response = connection.create_platform_endpoint(
            self.platform.arn,
            self.push_token,
            custom_user_data=custom_user_data
        )
        self.is_enabled = success = self.set_arn_from_response(response)
        # TODO: What is the app topic ?
        # if self.is_registered:
        #     self.platform.app_topic.register_device(self)
        self.save()
        return success

    @DefaultConnection
    def register_or_update(self, new_token=None, custom_user_data=u"",
                           connection=None):
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
    def deregister(self, connection=None):
        """
        :type connection: SNSConnection
        :param connection: the connection which should be used. if the argument isn't set there will be created a default connection
        :return:
        """
        if not self.is_registered:
            raise SNSNotCreatedException
        # ToDo: Delete from topics as well
        success = connection.delete_endpoint(self.arn)
        if success:
            self.arn = None
            self.save()
        return success

    @DefaultConnection
    def send_message(self, message, connection=None):
        return connection.publish(message=message, target_arn=self.arn)

    @PushLogger
    @DefaultConnection
    def send(self, push_message, connection=None):
        """
        :type connection: SNSConnection
        :param connection: the connection which should be used. if the argument isn't set there will be created a default connection
        :return:
        """
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
        :param connection: the connection which should be used. if the argument isn't set there will be created a default connection
        :return:
        """

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
        choices=AVAILABLE_PLATFORMS.items()
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
        if self.platform in ['APNS', 'APN_SANDBOX']:
            return APNPlatformStrategy(self)
        elif self.platform in ['GCM']:
            return GCMPlatformStrategy(self)

    @property
    def name(self):
        return u"_".join([self.app_name, self.platform]).lower()

    @property
    def resource_name(self):
        return 'PlatformApplication'

    @property
    def app_topic(self):
        if not self._app_topic:
            topic = Topic(self.app_name)
            if topic.register():
                self._app_topic = topic
        return self._app_topic

    @property
    def attributes(self):
        return {
            "PlatformCredential": self.credential,
            "PlatformPrincipal": self.principal
        }

    @DefaultConnection
    def delete(self, using=None, connection=None):
        if not self.deregister(connection):
            logger.warn("Could not unregister platform on delete.")
        super().delete(using)

    @DefaultConnection
    def register(self, connection=None):
        """
        Adds an app to SNS. Apps are per platform. The name of a sns application is app_platform

        :type connection: SNSConnection
        :param connection: the connection which should be used. if the argument isn't set there will be created a default connection
        :rtype bool:
        :return:
        """

        response = connection.create_platform_application(
            self.name,
            self.platform,
            self.attributes
        )
        return self.set_arn_from_response(response)

    @DefaultConnection
    def deregister(self, connection=None):
        """
        :type connection: SNSConnection
        :param connection: the connection which should be used. if the argument isn't set there will be created a default connection
        :return:
        """
        if not self.is_registered:
            raise SNSNotCreatedException
        success = connection.delete_platform_application(self.arn)
        if success:
            self.arn = None
            self.save()
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


class PlatformStrategy(metaclass=ABCMeta):
    def __init__(self, platform_application):
        super().__init__()
        self.platform = platform_application

    def format_payload(self, data):
        return {self.platform.platform: json.dumps(data)}


class APNPlatformStrategy(PlatformStrategy):
    def format_payload(self, message):
        """
        :type message: PushMessage
        :param message:
        :return:
        """

        payload = format_push(
            message.badge_count,
            message.context,
            message.context_id,
            message.has_new_content,
            message.message, message.sound
        )

        if message.extra_payload:
            payload.update(message.extra_payload)

        return super(
            APNPlatformStrategy,
            self
        ).format_payload(payload)


class GCMPlatformStrategy(PlatformStrategy):
    def format_payload(self, message):
        """
        :type data: PushMessage
        :param data:
        :return:
        """
        data = message.as_dict()
        h = hash(frozenset(data.items()))
        return super(
            GCMPlatformStrategy,
            self
        ).format_payload({"collapse_key": h, "data": data})


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

    def delete(self, using=None, connection=None):
        if not self.deregister(connection):
            logger.warn("Could not unregister topic on delete.")
        super().delete(using)

    @DefaultConnection
    def register(self, connection=None):
        response = connection.create_topic(self.full_name)
        return self.set_arn_from_response(response)

    @DefaultConnection
    def deregister(self, connection=None):
        if not self.is_registered:
            raise SNSNotCreatedException
        success = connection.delete_topic(self.arn)
        if success:
            self.arn = None
            self.save()
        return success

    @DefaultConnection
    def register_device(self, device, connection=None):
        """
        :type device: Device
        :param device:
        :type connection: SNSConnection
        :param connection: the connection which should be used. if the argument isn't set there will be created a default connection
        :rtype bool:
        :return:
        """
        if not (self.is_registered and device.is_registered):
            raise SNSNotCreatedException
        subscription, created = Subscription.objects.get_or_create(
            device=device,
            topic=self,
        )
        success = subscription.register(connection)
        subscription.save()
        return success

    @DefaultConnection
    def deregister_device(self, device, connection=None):
        subscription = Subscription.objects.get(
            device=device,
            topic=self
        )
        subscription.delete(connection=connection)
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
    def delete(self, using=None, connection=None):
        if not self.deregister(connection):
            logger.warn("Could not unregister subscription on delete.")
        super().delete(using)

    @DefaultConnection
    def register(self, connection=None):
        if not self.device.is_registered:
            success = self.device.register()
            if not success:
                return success
        if not self.topic.is_registered:
            success = self.topic.register()
            if not success:
                return success

        success = connection.subscribe(
            topic=self.topic.arn,
            endpoint=self.device.arn,
            protocol="application"
        )
        self.set_arn_from_response(success)
        self.save()

    @DefaultConnection
    def deregister(self, connection=None):
        if not self.is_registered:
            return False
        success =  connection.unsubscribe(self.arn)
        if success:
            self.arn = None
            self.save()
        return success


def format_push(badgeCount, context, context_id, has_new_content, message,
                sound):
    if message:
        message = trim_message(message)

    payload = {
        'aps': {
            "content-available": has_new_content,
        },
        "ctx": context,
        "id": context_id
    }

    if message and len(message) > 0:
        payload['aps']['alert'] = message

    if not badgeCount is None:
        payload['aps'].update({
            "badge": badgeCount,
        })

    if not sound is None:
        payload['aps'].update({
            'sound': sound,
        })

    return payload


def trim_message(message):
    import sys

    if sys.getsizeof(message) > 140:
        while sys.getsizeof(message) > 140:
            message = message[:-3]
        message += '...'
    return message