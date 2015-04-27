from abc import ABCMeta, abstractproperty, abstractmethod
import json
from boto.exception import BotoServerError
from django.conf import settings
import re
from .utils import DefaultConnection, PushLogger, APP_PREFIX
from django.db import models


class SNSCRUDMixin(object):
    __metaclass__ = ABCMeta

    def __init__(self, resource_name):
        super(SNSCRUDMixin, self).__init__()
        self.resource_name = resource_name
        self.arn = None

    def __eq__(self, other):
        if type(other) is type(self):
            return self.arn == other.arn
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

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
            self.arn = response_dict[self.response_key][self.result_key][self.arn_key]
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


class SNSDevice(SNSCRUDMixin):
    def __init__(self, platform, token, arn=None, is_enabled=False):
        """
        :type platform: SNSPlatformApplication
        :param platform:
        :type token: unicode
        :param token:
        :return:
        """
        super(SNSDevice, self).__init__("PlatformEndpoint")
        self.token = token
        self.platform = platform
        self.is_enabled = is_enabled
        self.arn = arn

    @property
    def arn_key(self):
        return "EndpointArn"

    @DefaultConnection
    def register(self, custom_user_data=u"", connection=None):
        if not self.platform.is_registered:
            success = self.platform.register(connection)
            if not success:
                return success
        response = connection.create_platform_endpoint(self.platform.arn, self.token, custom_user_data=custom_user_data)
        self.is_enabled = success = self.set_arn_from_response(response)
        if self.is_registered:
            self.platform.app_topic.register_device(self)
        return success

    @DefaultConnection
    def register_or_update(self, new_token=None, custom_user_data=u"", connection=None):
        if self.is_registered:
            result = self.update(new_token, custom_user_data, connection)
        else:
            try:
                result = self.register(custom_user_data, connection)
            #    Heavily inspired by http://stackoverflow.com/a/28316993/270265
            except BotoServerError as err:
                result_re = re.compile(r'Endpoint(.*)already', re.IGNORECASE)
                result = result_re.search(err.message)
                if result:
                    arn = result.group(0).replace('Endpoint ','').replace(' already','')
                    self.arn = arn
                    self.update(new_token, custom_user_data, connection)
        return result

    @DefaultConnection
    def delete(self, connection=None):
        """
        :type connection: SNSConnection
        :param connection: the connection which should be used. if the argument isn't set there will be created a default connection
        :return:
        """
        if not self.is_registered:
            raise SNSNotCreatedException

        return connection.delete_endpoint(self.arn)

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
        return connection.publish(message=json_string, target_arn=self.arn, message_structure="json")


    @DefaultConnection
    def update(self, new_token=None, custom_user_data=u"", connection=None):
        """
        :type connection: SNSConnection
        :param connection: the connection which should be used. if the argument isn't set there will be created a default connection
        :return:
        """

        new_token = new_token if new_token else self.token
        attributes = {"Enabled": True, "Token": new_token}
        if custom_user_data:
            attributes["CustomUserData"] = custom_user_data
        answer = connection.set_endpoint_attributes(self.arn, attributes)
        self.is_enabled = True
        self.token = new_token
        return answer

    def sign(self, push_message):
        push_message.receiver_arn = self.arn
        push_message.message_type = PushMessage.MESSAGE_TYPE_TOPIC

    @classmethod
    def create_from_endpoints(cls, platform, endpoints):
        devices = list()
        for endpoint in endpoints:
            attributes = endpoint[u'Attributes']
            token = attributes[u'Token']
            is_enabled = attributes[u"Enabled"].lower() == u'true'
            arn = endpoint[u'EndpointArn']
            device = cls(platform, token)
            device.arn = arn
            device.is_enabled = is_enabled
            devices.append(device)
        return devices


class SNSPlatformApplication(SNSCRUDMixin):
    __metaclass__ = ABCMeta

    def __init__(self, app_name=APP_PREFIX):
        super(SNSPlatformApplication, self).__init__("PlatformApplication")
        self.app_name = app_name
        self._app_topic = None

    @property
    def name(self):
        return u"_".join([self.app_name, self.platform]).lower()

    @property
    def app_topic(self):
        if not self._app_topic:
            topic = Topic(self.app_name)
            if topic.register():
                self._app_topic = topic
        return self._app_topic

    @abstractproperty
    def platform(self):
        """
        :rtype: unicode
        :return: the platform name
        """
        pass

    @abstractproperty
    def credential(self):
        pass

    @abstractproperty
    def principal(self):
        pass

    @property
    def attributes(self):
        return {"PlatformCredential": self.credential,
                "PlatformPrincipal": self.principal
        }

    @DefaultConnection
    def register(self, connection=None):
        """
        Adds an app to SNS. Apps are per platform. The name of a sns application is app_platform

        :type connection: SNSConnection
        :param connection: the connection which should be used. if the argument isn't set there will be created a default connection
        :rtype bool:
        :return:
        """

        response = connection.create_platform_application(self.name, self.platform, self.attributes)
        return self.set_arn_from_response(response)

    @DefaultConnection
    def delete(self, connection=None):
        """
        :type connection: SNSConnection
        :param connection: the connection which should be used. if the argument isn't set there will be created a default connection
        :return:
        """
        if not self.is_registered:
            raise SNSNotCreatedException
        return connection.delete_platform_application(self.arn)

    @DefaultConnection
    def all_devices(self, connection=None):
        devices_list = list()

        def get_next(nexttoken):
            response = connection.list_endpoints_by_platform_application(platform_application_arn=self.arn,
                                                                         next_token=nexttoken)
            result = response[u'ListEndpointsByPlatformApplicationResponse'][
                u'ListEndpointsByPlatformApplicationResult']
            devices = result[u'Endpoints']
            devices_list.extend(SNSDevice.create_from_endpoints(self, devices))
            return result[u'NextToken']

        next_token = get_next(None)

        while next_token:
            next_token = get_next(next_token)

        return devices_list

    def format_payload(self, data):
        return {self.platform: json.dumps(data)}


class APNApplication(SNSPlatformApplication):
    @property
    def platform(self):
        return settings.SCARFACE_APNS_MODE

    @property
    def credential(self):
        return settings.SCARFACE_APNS_PRIVATE_KEY

    @property
    def principal(self):
        return settings.SCARFACE_APNS_CERTIFICATE

    def format_payload(self, message):
        """
        :type message: PushMessage
        :param message:
        :return:
        """

        payload = format_push(message.badge_count, message.context, message.context_id, message.has_new_content,
                              message.message, message.sound)
        if message.extra_payload:
            payload.update(message.extra_payload)
        return super(APNApplication, self).format_payload(payload)


class GCMApplication(SNSPlatformApplication):
    @property
    def platform(self):
        return u"GCM"

    @property
    def credential(self):
        return settings.SCARFACE_GCM_API_KEY

    @property
    def principal(self):
        return None

    def format_payload(self, message):
        """
        :type data: PushMessage
        :param data:
        :return:
        """
        data = message.as_dict()
        h = hash(frozenset(data.items()))
        return super(GCMApplication, self).format_payload({"collapse_key": h, "data": data})


class Topic(SNSCRUDMixin):
    def __init__(self, name):
        super(Topic, self).__init__("Topic")
        self.name = name

    @DefaultConnection
    def register(self, connection=None):
        response = connection.create_topic(self.name)
        return self.set_arn_from_response(response)

    @DefaultConnection
    def delete(self, connection=None):
        if not self.is_registered:
            raise SNSNotCreatedException
        return connection.delete_topic(self.arn)

    @DefaultConnection
    def register_device(self, device, connection=None):
        """
        :type device: SNSDevice
        :param device:
        :type connection: SNSConnection
        :param connection: the connection which should be used. if the argument isn't set there will be created a default connection
        :rtype bool:
        :return:
        """
        if not (self.is_registered and device.is_registered):
            raise SNSNotCreatedException
        success = connection.subscribe(topic=self.arn, endpoint=device.arn, protocol="application")
        return success

    @DefaultConnection
    def all_subscriptions(self, connection=None):
        subscriptions_list = list()

        def get_next(nexttoken):
            response = connection.get_all_subscriptions_by_topic(topic=self.arn, next_token=nexttoken)
            result = response["ListSubscriptionsByTopicResponse"]["ListSubscriptionsByTopicResult"]
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
    def send(self, push_message, platforms, connection=None):
        """

        :type push_message: PushMessage
        :param push_message:
        :type platforms:list
        :param platforms:
        :return:
        """
        payload = dict()
        for platform in platforms:
            payload.update(platform.format_payload(push_message))
        payload["default"] = push_message.message
        json_string = json.dumps(payload)
        return connection.publish(message=json_string, topic=self.arn, message_structure="json")


class SNSNotCreatedException(Exception):
    message = "Register the instance before deleting it by calling register()"


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

    # def __init__(self, message='', context='default', context_id='none', badge_count=0, sound=None, has_new_content=0,
    # extra_payload=None):
    # super(PushMessage, self).__init__(message, context, context_id, badge_count, sound, has_new_content,
    # extra_payload)
    #     self.sound = sound
    #     self.message = message
    #     self.has_new_content = has_new_content
    #     self.context_id = context_id
    #     self.context = context
    #     self.badge_count = badge_count
    #     self.extra_payload = extra_payload

    def as_dict(self):
        d = {'message': self.message,
             'context': self.context,
             'context_id': self.context_id,
             'badge_count': self.badge_count,
             'sound': self.sound,
             'has_new_content': self.has_new_content}
        if self.extra_payload:
            d.update(self.extra_payload)
        return d


def format_push(badgeCount, context, context_id, has_new_content, message, sound):
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
