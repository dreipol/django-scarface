"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import unittest
from unittest.mock import Mock

from boto.exception import BotoServerError
from django.test import TestCase
from scarface.exceptions import PlatformNotSupported
from scarface.platform_strategy import get_strategies, PlatformStrategy
from scarface.settings import SCARFACE_DEFAULT_PLATFORM_STRATEGIES
from scarface.signals import instance_deleted
from .models import Application, Platform, Topic, Device, Subscription, \
    PushMessage
from .utils import DefaultConnection

TEST_ARN_TOKEN = 'test_arn_token'
TEST_PUSH_TOKEN = 'test_push_token'
TEST_IOS_DEVICE_ID = 'test_ios_device_id'
TEST_ANDROID_DEVICE_ID = 'test_android_device_id'
TEST_DEVICE_ID = 'test_device_id'
TEST_CREDENTIAL = 'test_credential'
TEST_PRINCIPAL = 'test_principal'
TEST_ARN_TOKEN_GCM = 'test_arn_token_gcm'
TEST_ARN_TOKEN_APNS = 'test_arn_token_apns'
TEST_ARN_TOKEN_IOS_DEVICE = 'test_arn_ios_device'
TEST_ARN_TOKEN_ANDROID_DEVICE = 'test_arn_android_device'
TEST_ARN_TOKEN_TOPIC = 'test_topic_arn'
TEST_ARN_TOKEN_SUBSCRIPTION = 'test_token_subscription'
TEST_ARN_TOKEN_PLATFORM = 'test_arn_token_platform'
TEST_TOPIC_NAME = 'test_topic_name'
TEST_MESSAGE = 'test_message'
TEST_APPLICATION_NAME = 'test_applicaiton'


class BaseTestCase(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @property
    def application(self):
        return Application.objects.create(
                name=TEST_APPLICATION_NAME
        )

    def get_apns_platform(self, application):
        return Platform.objects.create(
                platform='APNS',
                application=application,
                credential=TEST_CREDENTIAL,
                principal=TEST_PRINCIPAL,
                arn=TEST_ARN_TOKEN_APNS
        )

    def get_gcm_platform(self, application):
        return Platform.objects.create(
                platform='GCM',
                application=application,
                credential=TEST_CREDENTIAL,
                principal=TEST_PRINCIPAL,
                arn=TEST_ARN_TOKEN_GCM
        )

    def get_ios_device(self, platform):
        return Device.objects.create(
                device_id=TEST_IOS_DEVICE_ID,
                platform=platform,
                push_token=TEST_PUSH_TOKEN,
                arn=TEST_ARN_TOKEN_IOS_DEVICE
        )

    def get_android_device(self, platform):
        return Device.objects.create(
                device_id=TEST_ANDROID_DEVICE_ID,
                platform=platform,
                push_token=TEST_PUSH_TOKEN,
                arn=TEST_ARN_TOKEN_ANDROID_DEVICE
        )

    def get_topic(self, application):
        return Topic.objects.create(
                name=TEST_TOPIC_NAME,
                application=application,
                arn=TEST_ARN_TOKEN_TOPIC,
        )


class ApplicationTestCase(BaseTestCase):
    def test_get_platform(self):
        app = self.application
        exception = False

        try:
            app.get_platform('GCN')
        except PlatformNotSupported:
            exception = True
        self.assertTrue(exception)

        exception = False
        try:
            app.get_platform('APNS')
        except PlatformNotSupported:
            exception = True
        self.assertTrue(exception)

        platform_apns = self.get_apns_platform(app)

        exception = False
        try:
            app.get_platform('APNS')
        except PlatformNotSupported:
            exception = True
        self.assertFalse(exception)

        exception = False
        try:
            app.get_platform('GCM')
        except PlatformNotSupported:
            exception = True
        self.assertTrue(exception)

        platform_apns = self.get_gcm_platform(app)

        exception = False
        try:
            app.get_platform('APNS')
        except PlatformNotSupported:
            exception = True
        self.assertFalse(exception)

        exception = False
        try:
            app.get_platform('GCM')
        except PlatformNotSupported:
            exception = True
        self.assertFalse(exception)


class PlatformTestCase(BaseTestCase):
    def test_register_arn_platform(self):
        PLATFORM = 'APNS'
        application = self.application

        connection = Mock()
        platform = Platform.objects.create(
                platform=PLATFORM,
                application=application,
                credential=TEST_CREDENTIAL,
                principal=TEST_PRINCIPAL,
        )

        connection.create_platform_application.return_value = {
            'CreatePlatformApplicationResponse': {
                'CreatePlatformApplicationResult': {
                    'PlatformApplicationArn': TEST_ARN_TOKEN_PLATFORM
                }
            }
        }

        platform.register(connection)
        platform.save()

        self.assertEqual(TEST_ARN_TOKEN_PLATFORM, platform.arn)
        connection.create_platform_application.assert_called_once_with(
                "{0}_{1}".format(application.name, PLATFORM).lower(),
                PLATFORM,
                {
                    'PlatformCredential': TEST_CREDENTIAL,
                    'PlatformPrincipal': TEST_PRINCIPAL
                }
        )

    def test_register_gcm_platform(self):
        PLATFORM = 'GCM'
        application = self.application
        platform = Platform.objects.create(
                platform=PLATFORM,
                application=application,
                credential=TEST_CREDENTIAL,
        )

        connection = Mock()
        connection.create_platform_application.return_value = {
            'CreatePlatformApplicationResponse': {
                'CreatePlatformApplicationResult': {
                    'PlatformApplicationArn': TEST_ARN_TOKEN_PLATFORM
                }
            }
        }

        platform.register(connection)
        platform.save()

        self.assertEqual(TEST_ARN_TOKEN_PLATFORM, platform.arn)
        connection.create_platform_application.assert_called_once_with(
                "{0}_{1}".format(application.name, PLATFORM).lower(),
                PLATFORM,
                {
                    'PlatformCredential': TEST_CREDENTIAL,
                    'PlatformPrincipal': None
                }
        )

    def test_deregister(self):
        app = self.application
        platform = self.get_apns_platform(app)
        connection = Mock()

        platform.deregister(connection)
        connection.delete_platform_application.assert_called_once_with(
                TEST_ARN_TOKEN_APNS
        )

        self.assertFalse(platform.is_registered)

    @unittest.skip(
            "Post delete signal and mock connection don't work together.")
    def test_delete(self):
        app = self.application
        platform = self.get_apns_platform(app)
        connection = Mock()
        platform.delete(connection=connection)

        connection.delete_platform_application.assert_called_once_with(
                TEST_ARN_TOKEN_APNS
        )

    def test_all_devices(self):
        ARN_1 = 'arn_1'
        ARN_2 = 'arn_2'
        ARN_3 = 'arn_3'
        ENDPOINT_LIST = [
            {'EndpointArn': ARN_1},
            {'EndpointArn': ARN_2},
            {'EndpointArn': ARN_3},
        ]
        app = self.application
        platform = self.get_apns_platform(app)

        def create_device(id, arn):
            return Device.objects.create(
                    device_id=id,
                    platform=platform,
                    push_token=TEST_PUSH_TOKEN,
                    arn=arn
            )

        device_1 = create_device('1', 'arn_1')
        device_2 = create_device('2', 'arn_2')
        device_3 = create_device('3', 'arn_3')

        connection = Mock()
        connection.list_endpoints_by_platform_application.return_value = {
            'ListEndpointsByPlatformApplicationResponse': {
                'ListEndpointsByPlatformApplicationResult': {
                    'Endpoints': ENDPOINT_LIST,
                    'NextToken': None
                }
            }
        }

        devices = platform.all_devices(connection)

        connection.list_endpoints_by_platform_application(
                platform_application_arn=TEST_ARN_TOKEN_APNS,
                next_token=None
        )
        self.assertEqual(len(devices), 3)

    def test_send_message(self):
        app = self.application
        platform = self.get_apns_platform(app)
        device = Device.objects.create(
                device_id=TEST_IOS_DEVICE_ID,
                platform=platform,
                push_token=TEST_PUSH_TOKEN,
                arn=TEST_ARN_TOKEN_IOS_DEVICE
        )
        message = PushMessage(
                badge_count=1,
                context='url_alert',
                context_id='none',
                has_new_content=True,
                message="Hello world!",
                sound="default"
        )
        connection = Mock()
        device.send_message(message, connection=connection)
        connection.publish.assert_called_once_with(
            message=message,
            target_arn=TEST_ARN_TOKEN_IOS_DEVICE
        )


class DeviceTestCase(BaseTestCase):
    def test_register_ios_device(self):
        connection = Mock()
        application = self.application
        platform = self.get_apns_platform(application)

        connection.create_platform_endpoint.return_value = {
            'CreatePlatformEndpointResponse': {
                'CreatePlatformEndpointResult': {
                    'EndpointArn': TEST_ARN_TOKEN_IOS_DEVICE
                }
            }
        }

        device = Device.objects.create(
                device_id=TEST_DEVICE_ID,
                push_token=TEST_PUSH_TOKEN,
                platform=platform
        )

        device.register(connection=connection)

        connection.create_platform_endpoint.assert_called_once_with(
                TEST_ARN_TOKEN_APNS,
                TEST_PUSH_TOKEN,
                custom_user_data="",
        )
        self.assertEqual(device.arn, TEST_ARN_TOKEN_IOS_DEVICE)
        self.assertTrue(device.is_registered)

    def test_register_android_device(self):
        connection = Mock()
        application = self.application
        platform = self.get_gcm_platform(application)

        connection.create_platform_endpoint.return_value = {
            'CreatePlatformEndpointResponse': {
                'CreatePlatformEndpointResult': {
                    'EndpointArn': TEST_ARN_TOKEN_ANDROID_DEVICE
                }
            }
        }

        device = Device.objects.create(
                device_id=TEST_DEVICE_ID,
                platform=platform,
                push_token=TEST_PUSH_TOKEN,
        )

        device.register(connection=connection)

        connection.create_platform_endpoint.assert_called_once_with(
                TEST_ARN_TOKEN_GCM,
                TEST_PUSH_TOKEN,
                custom_user_data="",
        )
        self.assertEqual(device.arn, TEST_ARN_TOKEN_ANDROID_DEVICE)
        self.assertTrue(device.is_registered)

    def test_deregister(self):
        app = self.application
        platform = self.get_gcm_platform(app)
        device = self.get_android_device(platform)
        connection = Mock()
        connection.delete_endpoint.return_value = True

        device.deregister(connection)

        connection.delete_endpoint.assert_called_once_with(
                TEST_ARN_TOKEN_ANDROID_DEVICE
        )
        self.assertFalse(device.is_registered)

    @unittest.skip(
            "Post delete signal and mock connection don't work together.")
    def test_delete(self):
        app = self.application
        platform = self.get_gcm_platform(app)
        device = self.get_android_device(platform)
        connection = Mock()
        connection.delete_endpoint.return_value = True

        device.delete()

        connection.delete_endpoint.assert_called_once_with(
                TEST_ARN_TOKEN_ANDROID_DEVICE
        )

    def test_send_message(self):
        app = self.application
        platform = self.get_gcm_platform(app)
        device = self.get_android_device(platform)
        connection = Mock()
        connection.publish.return_value = True

        device.send_message(TEST_MESSAGE, connection=connection)

        connection.publish.assert_called_once_with(
                message=TEST_MESSAGE,
                target_arn=TEST_ARN_TOKEN_ANDROID_DEVICE
        )

    def test_update(self):
        NEW_PUSH_TOKEN = 'new_push_token'
        USER_DATA = 'user_data'

        app = self.application
        platform = self.get_gcm_platform(app)
        device = self.get_android_device(platform)
        connection = Mock()
        connection.set_endpoint_attributes.return_value = True

        device.update(NEW_PUSH_TOKEN, USER_DATA, connection)

        connection.set_endpoint_attributes.assert_called_once_with(
                TEST_ARN_TOKEN_ANDROID_DEVICE,
                {
                    'Enabled': True,
                    'Token': NEW_PUSH_TOKEN,
                    'CustomUserData': USER_DATA
                }
        )


class TopicTestCase(BaseTestCase):
    def test_register(self):
        application = self.application

        topic = Topic.objects.create(
                name=TEST_TOPIC_NAME,
                application=application,
        )
        topic.delete()

    def test_register(self):
        application = self.application

        topic = Topic.objects.create(
                name=TEST_TOPIC_NAME,
                application=application,
        )
        connection = Mock()
        connection.create_topic.return_value = {
            'CreateTopicResponse': {
                'CreateTopicResult': {
                    'TopicArn': TEST_ARN_TOKEN_TOPIC
                }
            }
        }

        topic.register(connection=connection)

        self.assertEqual(topic.arn, TEST_ARN_TOKEN_TOPIC)
        connection.create_topic.assert_called_once_with(
                '_'.join([TEST_APPLICATION_NAME, TEST_TOPIC_NAME])
        )

    def test_deregister(self):
        app = self.application
        topic = Topic.objects.create(
                name=TEST_TOPIC_NAME,
                application=app,
                arn=TEST_ARN_TOKEN_TOPIC
        )

        connection = Mock()
        topic.deregister(connection)

        connection.delete_topic.assert_called_once_with(
                TEST_ARN_TOKEN_TOPIC
        )
        self.assertFalse(topic.is_registered)

    @unittest.skip(
            "Post delete signal and mock connection don't work together.")
    def test_delete(self):
        app = self.application
        topic = Topic.objects.create(
                name=TEST_TOPIC_NAME,
                application=app,
                arn=TEST_ARN_TOKEN_TOPIC
        )

        connection = Mock()
        topic.delete(connection=connection)

        connection.delete_topic.assert_called_once_with(
                TEST_ARN_TOKEN_TOPIC
        )

    def test_register_device(self):
        app = self.application
        platform = self.get_apns_platform(app)
        topic = self.get_topic(app)
        device = self.get_ios_device(platform)
        connection = Mock()
        connection.subscribe.return_value = {
            'SubscribeResponse': {
                'SubscribeResult': {
                    'SubscriptionArn': TEST_ARN_TOKEN_SUBSCRIPTION
                }
            }
        }

        topic.register_device(device, connection)

        connection.subscribe.assert_called_once_with(
                topic=TEST_ARN_TOKEN_TOPIC,
                endpoint=TEST_ARN_TOKEN_IOS_DEVICE,
                protocol='application'
        )

        try:
            subscription = Subscription.objects.get(
                    device=device,
                    topic=topic
            )
            self.assertEqual(subscription.arn, TEST_ARN_TOKEN_SUBSCRIPTION)
        except Subscription.DoesNotExist:
            self.assertTrue(False)

    def test_deregister_device(self):
        app = self.application
        platform = self.get_apns_platform(app)
        topic = self.get_topic(app)
        device = self.get_ios_device(platform)
        connection = Mock()
        connection.subscribe.return_value = {
            'SubscribeResponse': {
                'SubscribeResult': {
                    'SubscriptionArn': TEST_ARN_TOKEN_SUBSCRIPTION
                }
            }
        }
        connection.unsubscribe.return_value = True
        topic.register_device(device, connection)
        subscription_arn = Subscription.objects.get(
                device=device,
                topic=topic
        ).arn

        try:
            topic.deregister_device(device, connection)
        except BotoServerError as e:
            pass

        connection.unsubscribe.assert_called_once_with(
                subscription_arn
        )
        try:
            subscription = Subscription.objects.get(
                    device=device,
                    topic=topic
            )
            self.assertTrue(False)
        except Subscription.DoesNotExist:
            pass

    def test_send(self):
        MESSAGE = 'test_message'
        app = self.application
        platform_apns = self.get_apns_platform(app)
        platform_gcm = self.get_gcm_platform(app)
        topic = self.get_topic(app)
        connection = Mock()
        message = PushMessage.objects.create(
                message=MESSAGE
        )

        topic.send(message, connection)

        self.assertTrue(connection.publish.called)


class TestStrategy(PlatformStrategy):
    id = 'test'
    pass


class StrategyImportTestCase(TestCase):
    def test_get_strategies(self):
        strategies = get_strategies()
        self.assertEqual(len(strategies),
                         len(SCARFACE_DEFAULT_PLATFORM_STRATEGIES))

    def test_get_strategies_custom(self):
        from django.conf import settings
        settings.SCARFACE_PLATFORM_STRATEGIES = [
            'scarface.tests.TestStrategy'
        ]
        strategies = get_strategies()
        self.assertEqual(
                len(strategies),
                len(
                        SCARFACE_DEFAULT_PLATFORM_STRATEGIES
                        + settings.SCARFACE_PLATFORM_STRATEGIES
                )
        )


@DefaultConnection
def connection_test(a=None, connection=None):
    return a, connection


    # class ExtractKeysCommand(TestCase):
    #     def test_command_output(self):
    #         out = StringIO()
    #         call_command("extract_keys", file="local_push.p12", password="bazinga",
    #                      stdout=out)
    #         out_getvalue = out.getvalue()
    #         self.assertIn('SCARFACE_APNS_CERTIFICATE', out_getvalue)