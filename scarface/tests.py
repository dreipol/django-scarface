"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
from unittest.mock import Mock, MagicMock
from six import StringIO
from django.test import TestCase
from django.core.management import call_command
from scarface.exceptions import PlatformNotSupported
from .models import Application, Platform, Topic, Device, IOS, \
    ANDROID, Subscription, PushMessage
from .utils import get_sns_connection, DefaultConnection

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

    def get_ios_device(self, application):
        return Device.objects.create(
            device_id=TEST_IOS_DEVICE_ID,
            application=application,
            push_token=TEST_PUSH_TOKEN,
            os=IOS,
            arn=TEST_ARN_TOKEN_IOS_DEVICE
        )

    def get_android_device(self, application):
        return Device.objects.create(
            device_id=TEST_ANDROID_DEVICE_ID,
            application=application,
            push_token=TEST_PUSH_TOKEN,
            os=ANDROID,
            arn=TEST_ARN_TOKEN_ANDROID_DEVICE
        )

    def get_topic(self, application):
        return Topic.objects.create(
            name=TEST_TOPIC_NAME,
            application=application,
            arn=TEST_ARN_TOKEN_TOPIC,
        )

    @property
    def topic_name(self):
        return self.app_name + "topic"


class ApplicationTestCase(BaseTestCase):
    def test_platform_for_device(self):
        app = self.application
        device_ios = self.get_ios_device(app)
        device_android = self.get_android_device(app)
        exception = False

        try:
            app.platform_for_device(device_ios)
        except PlatformNotSupported:
            exception = True
        self.assertTrue(exception)

        exception = False
        try:
            app.platform_for_device(device_android)
        except PlatformNotSupported:
            exception = True
        self.assertTrue(exception)

        platform_apns = self.get_apns_platform(app)

        exception = False
        try:
            app.platform_for_device(device_ios)
        except PlatformNotSupported:
            exception = True
        self.assertFalse(exception)

        exception = False
        try:
            app.platform_for_device(device_android)
        except PlatformNotSupported:
            exception = True
        self.assertTrue(exception)

        platform_apns = self.get_gcm_platform(app)

        exception = False
        try:
            app.platform_for_device(device_ios)
        except PlatformNotSupported:
            exception = True
        self.assertFalse(exception)

        exception = False
        try:
            app.platform_for_device(device_android)
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
                application=app,
                push_token=TEST_PUSH_TOKEN,
                os=IOS,
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


class DeviceTestCase(BaseTestCase):
    def test_register_ios_device(self):
        connection = Mock()
        application = self.application
        get_platform = Mock()
        get_platform.return_value = self.get_apns_platform(application)
        application.platform_for_device = get_platform

        connection.create_platform_endpoint.return_value = {
            'CreatePlatformEndpointResponse': {
                'CreatePlatformEndpointResult': {
                    'EndpointArn': TEST_ARN_TOKEN_IOS_DEVICE
                }
            }
        }

        device = Device.objects.create(
            device_id=TEST_DEVICE_ID,
            application=application,
            push_token=TEST_PUSH_TOKEN,
            os=IOS
        )

        device.register(connection=connection)

        application.platform_for_device.assert_called_once_with(device)
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
        get_platform = Mock()
        get_platform.return_value = self.get_gcm_platform(application)
        application.platform_for_device = get_platform

        connection.create_platform_endpoint.return_value = {
            'CreatePlatformEndpointResponse': {
                'CreatePlatformEndpointResult': {
                    'EndpointArn': TEST_ARN_TOKEN_ANDROID_DEVICE
                }
            }
        }

        device = Device.objects.create(
            device_id=TEST_DEVICE_ID,
            application=application,
            push_token=TEST_PUSH_TOKEN,
            os=ANDROID
        )

        device.register(connection=connection)

        application.platform_for_device.assert_called_once_with(device)
        connection.create_platform_endpoint.assert_called_once_with(
            TEST_ARN_TOKEN_GCM,
            TEST_PUSH_TOKEN,
            custom_user_data="",
        )
        self.assertEqual(device.arn, TEST_ARN_TOKEN_ANDROID_DEVICE)
        self.assertTrue(device.is_registered)

    def test_deregister(self):
        app = self.application
        device = self.get_android_device(app)
        connection = Mock()
        connection.delete_endpoint.return_value = True

        device.deregister(connection)

        connection.delete_endpoint.assert_called_once_with(
            TEST_ARN_TOKEN_ANDROID_DEVICE
        )
        self.assertFalse(device.is_registered)

    def test_send_message(self):
        app = self.application
        device = self.get_android_device(app)
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
        device = self.get_android_device(app)
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
            application = app,
            arn=TEST_ARN_TOKEN_TOPIC
        )

        connection = Mock()
        topic.deregister(connection)

        connection.delete_topic.assert_called_once_with(
            TEST_ARN_TOKEN_TOPIC
        )
        self.assertFalse(topic.is_registered)

    def test_register_device(self):
        app = self.application
        platform = self.get_apns_platform(app)
        topic = self.get_topic(app)
        device = self.get_ios_device(app)
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
        device = self.get_ios_device(app)
        connection = Mock()
        connection.subscribe.return_value = {
            'SubscribeResponse': {
                'SubscribeResult': {
                    'SubscriptionArn': TEST_ARN_TOKEN_SUBSCRIPTION
                }
            }
        }
        topic.register_device(device, connection)
        subscription_arn = Subscription.objects.get(
            device=device,
            topic=topic
        ).arn

        topic.deregister_device(device, connection)

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



pass
# def tearDown(self):
# gcm_application = GCMApplication(self.app_name)
# gcm_application.register()
# self.resources.extend(gcm_application.all_devices())
# self.resources.append(gcm_application)
# for resource in self.resources:
#     resource.delete()

# def platform_test(self, platform):
#     result = platform.register()
#     self.resources.append(platform)
#     return result
#
# def create_apn_device(self):
#     app = APNApplication(self.app_name)
#     app.register()
#     device = SNSDevice(app, self.apn_token)
#     created = device.register()
#     self.resources.append(device)
#     return created, device
#
# def create_gcm_device(self):
#     gcm_application = GCMApplication(self.app_name)
#     gcm_application.register()
#     device = SNSDevice(gcm_application, self.gcm_token)
#     created = device.register()
#     self.resources.append(device)
#     return created, device
#
# def test_add_apn(self):
#     """
#     Test adding APN app
#     """
#     apn_platform = APNApplication(self.app_name)
#     result = self.platform_test(apn_platform)
#     self.assertTrue(result)
#
# def test_add_gcm(self):
#     result = self.platform_test(GCMApplication(self.app_name))
#     self.assertTrue(result)
#
# def test_delete_gcm(self):
#     gcm_application = GCMApplication(self.app_name)
#     gcm_application.register()
#     result = gcm_application.delete()
#     self.assertTrue(result)
#
# def test_delete_does_not_exist(self):
#     gcm_application = GCMApplication('test_no_app')
#     gcm_application.arn = 'arn:test_no_app'
#     self.assertRaises(BotoServerError, gcm_application.delete)
#
# def create_app_topic(self):
#     topic = Topic(self.topic_name)
#     success = topic.register()
#     self.resources.append(topic)
#     return success, topic
#
# def test_add_topic(self):
#     success, topic = self.create_app_topic()
#     self.assertTrue(topic)
#
# def test_delete_topic(self):
#     topic = Topic(self.topic_name)
#     topic.register()
#     result = topic.delete()
#     self.assertTrue(result)
#
# def test_add_gcm_device(self):
#     device = self.create_gcm_device()
#     self.assertTrue(device)
#
# def test_add_apn_device(self):
#     created, device = self.create_apn_device()
#     self.assertTrue(created)
#
# def test_list_devices(self):
#     gcm_application = GCMApplication(self.app_name)
#     gcm_application.register()
#     created, device = self.create_gcm_device()
#     devices = gcm_application.all_devices()
#     self.assertListEqual(devices, [device, ])
#
# def test_send_gcm_push(self):
#     created, device = self.create_gcm_device()
#     success = device.send(
#         PushMessage(badge_count=1, context='url_alert', context_id='none',
#                     has_new_content=True, message="Hello world!", sound="default"))
#     self.assertEqual(PushMessage.objects.all().count(), 1)
#
# def test_send_apn_push(self):
#     created, device = self.create_apn_device()
#     message = PushMessage(badge_count=1, context='url_alert', context_id='none', has_new_content=True,
#                           message="Hello world!", sound="default")
#     device.send(message)
#     self.assertEqual(PushMessage.objects.all().count(), 1)
#
# def test_add_to_app_topic(self):
#     created_apn, apn_device = self.create_apn_device()
#     created_gcm, gcm_device = self.create_gcm_device()
#     topic = gcm_device.platform.app_topic
#     subscriptions = topic.all_subscriptions()
#     gcm_devices = gcm_device.platform.all_devices()
#     apn_devices = apn_device.platform.all_devices()
#     gcm_devices.extend(apn_devices)
#     self.assertEqual(len(subscriptions), len(gcm_devices))
#
# def test_send_to_topic(self):
#     created, apn_device = self.create_apn_device()
#     created_gcm, gcm_device = self.create_gcm_device()
#     topic = gcm_device.platform.app_topic
#     message = PushMessage(badge_count=1, context='url_alert', context_id='none', has_new_content=True,
#                           message="Hello Topic!", sound="default")
#     topic.send(message, platforms=[gcm_device.platform, apn_device.platform])
#     self.assertEqual(PushMessage.objects.all().count(), 1)
#
# def test_update_with_same_token(self):
#     created, device = self.create_apn_device()
#     device_updated = device.update(self.apn_token)
#     self.assertIsNotNone(device_updated)
#
# def test_register_with_other_user_data(self):
#     created, device = self.create_apn_device()
#     self.assertRaises(BotoServerError, device.register, {"custom_user_data": "Hello world!"})
#
# def test_update_with_other_user_data(self):
#     created, device = self.create_apn_device()
#     result = device.update(custom_user_data="Hello world!")
#     self.assertIsNotNone(result)
#
# def test_register_or_update(self):
#     created, device = self.create_apn_device()
#     result = device.register_or_update(custom_user_data="Hello world!")
#     self.assertIsNotNone(result)
#
# @override_settings(SCARFACE_LOGGING_ENABLED=False)
# def test_disable_logging(self):
#     created, device = self.create_gcm_device()
#     device.send(PushMessage(badge_count=1, context='url_alert', context_id='none', has_new_content=True,
#                           message="Hello Topic!", sound="default"))
#     self.assertEqual(0,PushMessage.objects.all().count())


# class DefaultConnectionWrapperTestCase(TestCase):
#     def test_wrapper_empty(self):
#         a, connection = connection_test()
#         self.assertIsNotNone(connection)
#
#     def test_wrapper_first_is_set_as_arg(self):
#         a_input = 123
#         a, connection = connection_test(a_input)
#         self.assertIsNotNone(connection)
#         self.assertEqual(a_input, a)
#
#     def test_wrapper_first_is_set_as_kwarg(self):
#         a_input = 123
#         a, connection = connection_test(a=a_input)
#         self.assertIsNotNone(connection)
#         self.assertEqual(a_input, a)
#
#     def test_wrapper_connection_is_set_as_arg(self):
#         a_input = 123
#         connection_input = get_sns_connection()
#         a, connection = connection_test(a_input, connection_input)
#         self.assertTrue(connection_input is connection)
#         self.assertEqual(a_input, a)
#
#     def test_wrapper_connection_is_set_as_kwarg(self):
#         a_input = 123
#         connection_input = get_sns_connection()
#         a, connection = connection_test(a_input, connection=connection_input)
#         self.assertTrue(connection_input is connection)
#         self.assertEqual(a_input, a)
#
#     def test_wrapper_connection_is_set_none(self):
#         a_input = 123
#         a, connection = connection_test(a_input, connection=None)
#         self.assertIsNotNone(connection)
#         self.assertEqual(a_input, a)
#
#     def test_wrapper_connection_is_set_none_arg(self):
#         a_input = 123
#         a, connection = connection_test(a_input, None)
#         self.assertIsNotNone(connection)
#         self.assertEqual(a_input, a)


# @DefaultConnection
# def connection_test(a=None, connection=None):
#     return a, connection


    # class ExtractKeysCommand(TestCase):
    #     def test_command_output(self):
    #         out = StringIO()
    #         call_command("extract_keys", file="local_push.p12", password="bazinga",
    #                      stdout=out)
    #         out_getvalue = out.getvalue()
    #         self.assertIn('SCARFACE_APNS_CERTIFICATE', out_getvalue)