"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
from boto.exception import BotoServerError
from django.test import TestCase
from django.test.utils import override_settings
from six import StringIO
from .models import APNApplication, GCMApplication, Topic, SNSDevice, PushMessage
from .utils import get_sns_connection, DefaultConnection, APP_PREFIX
from django.core.management import call_command


class SNSAppManagement(TestCase):
    def setUp(self):
        self.app_name = APP_PREFIX
        self.resources = list()
        self.gcm_token = "APA91bEUOyAVwExNEL1HPbWRq1lNKWGm5v4agR0idJYghHshF59MTZ9zOYiIeJCL0zu2_m5vPxEwieR3gOih225kI42MO-Np239-L1QLxrOfSLJtzfQf7oI_SnO_ekmM6kPCcMPUlx5xQ6LU3vEZKhy-GpaQTgFfCA"
        self.apn_token = "40e2aca271e95cd974873d62bc7360c3e0b94e66194b350ad0b9cba4ed6ddcdb"

    @property
    def topic_name(self):
        return self.app_name + "topic"

    def tearDown(self):
        gcm_application = GCMApplication(self.app_name)
        gcm_application.register()
        self.resources.extend(gcm_application.all_devices())
        self.resources.append(gcm_application)
        for resource in self.resources:
            resource.delete()

    def platform_test(self, platform):
        result = platform.register()
        self.resources.append(platform)
        return result

    def create_apn_device(self):
        app = APNApplication(self.app_name)
        app.register()
        device = SNSDevice(app, self.apn_token)
        created = device.register()
        self.resources.append(device)
        return created, device

    def create_gcm_device(self):
        gcm_application = GCMApplication(self.app_name)
        gcm_application.register()
        device = SNSDevice(gcm_application, self.gcm_token)
        created = device.register()
        self.resources.append(device)
        return created, device

    def test_add_apn(self):
        """
        Test adding APN app
        """
        apn_platform = APNApplication(self.app_name)
        result = self.platform_test(apn_platform)
        self.assertTrue(result)

    def test_add_gcm(self):
        result = self.platform_test(GCMApplication(self.app_name))
        self.assertTrue(result)

    def test_delete_gcm(self):
        gcm_application = GCMApplication(self.app_name)
        gcm_application.register()
        result = gcm_application.delete()
        self.assertTrue(result)

    def test_delete_does_not_exist(self):
        gcm_application = GCMApplication('test_no_app')
        gcm_application.arn = 'arn:test_no_app'
        self.assertRaises(BotoServerError, gcm_application.delete)

    def create_app_topic(self):
        topic = Topic(self.topic_name)
        success = topic.register()
        self.resources.append(topic)
        return success, topic

    def test_add_topic(self):
        success, topic = self.create_app_topic()
        self.assertTrue(topic)

    def test_delete_topic(self):
        topic = Topic(self.topic_name)
        topic.register()
        result = topic.delete()
        self.assertTrue(result)

    def test_add_gcm_device(self):
        device = self.create_gcm_device()
        self.assertTrue(device)

    def test_add_apn_device(self):
        created, device = self.create_apn_device()
        self.assertTrue(created)

    def test_list_devices(self):
        gcm_application = GCMApplication(self.app_name)
        gcm_application.register()
        created, device = self.create_gcm_device()
        devices = gcm_application.all_devices()
        self.assertListEqual(devices, [device, ])

    def test_send_gcm_push(self):
        created, device = self.create_gcm_device()
        success = device.send(
            PushMessage(badge_count=1, context='url_alert', context_id='none',
                        has_new_content=True, message="Hello world!", sound="default"))
        self.assertEqual(PushMessage.objects.all().count(), 1)

    def test_send_apn_push(self):
        created, device = self.create_apn_device()
        message = PushMessage(badge_count=1, context='url_alert', context_id='none', has_new_content=True,
                              message="Hello world!", sound="default")
        device.send(message)
        self.assertEqual(PushMessage.objects.all().count(), 1)

    def test_add_to_app_topic(self):
        created_apn, apn_device = self.create_apn_device()
        created_gcm, gcm_device = self.create_gcm_device()
        topic = gcm_device.platform.app_topic
        subscriptions = topic.all_subscriptions()
        gcm_devices = gcm_device.platform.all_devices()
        apn_devices = apn_device.platform.all_devices()
        gcm_devices.extend(apn_devices)
        self.assertEqual(len(subscriptions), len(gcm_devices))

    def test_send_to_topic(self):
        created, apn_device = self.create_apn_device()
        created_gcm, gcm_device = self.create_gcm_device()
        topic = gcm_device.platform.app_topic
        message = PushMessage(badge_count=1, context='url_alert', context_id='none', has_new_content=True,
                              message="Hello Topic!", sound="default")
        topic.send(message, platforms=[gcm_device.platform, apn_device.platform])
        self.assertEqual(PushMessage.objects.all().count(), 1)

    def test_update_with_same_token(self):
        created, device = self.create_apn_device()
        device_updated = device.update(self.apn_token)
        self.assertIsNotNone(device_updated)

    def test_register_with_other_user_data(self):
        created, device = self.create_apn_device()
        self.assertRaises(BotoServerError, device.register, {"custom_user_data": "Hello world!"})

    def test_update_with_other_user_data(self):
        created, device = self.create_apn_device()
        result = device.update(custom_user_data="Hello world!")
        self.assertIsNotNone(result)

    def test_register_or_update(self):
        created, device = self.create_apn_device()
        result = device.register_or_update(custom_user_data="Hello world!")
        self.assertIsNotNone(result)

    @override_settings(SCARFACE_LOGGING_ENABLED=False)
    def test_disable_logging(self):
        created, device = self.create_gcm_device()
        device.send(PushMessage(badge_count=1, context='url_alert', context_id='none', has_new_content=True,
                              message="Hello Topic!", sound="default"))
        self.assertEqual(0,PushMessage.objects.all().count())

class DefaultConnectionWrapperTestCase(TestCase):
    def test_wrapper_empty(self):
        a, connection = connection_test()
        self.assertIsNotNone(connection)

    def test_wrapper_first_is_set_as_arg(self):
        a_input = 123
        a, connection = connection_test(a_input)
        self.assertIsNotNone(connection)
        self.assertEqual(a_input, a)

    def test_wrapper_first_is_set_as_kwarg(self):
        a_input = 123
        a, connection = connection_test(a=a_input)
        self.assertIsNotNone(connection)
        self.assertEqual(a_input, a)

    def test_wrapper_connection_is_set_as_arg(self):
        a_input = 123
        connection_input = get_sns_connection()
        a, connection = connection_test(a_input, connection_input)
        self.assertTrue(connection_input is connection)
        self.assertEqual(a_input, a)

    def test_wrapper_connection_is_set_as_kwarg(self):
        a_input = 123
        connection_input = get_sns_connection()
        a, connection = connection_test(a_input, connection=connection_input)
        self.assertTrue(connection_input is connection)
        self.assertEqual(a_input, a)

    def test_wrapper_connection_is_set_none(self):
        a_input = 123
        a, connection = connection_test(a_input, connection=None)
        self.assertIsNotNone(connection)
        self.assertEqual(a_input, a)

    def test_wrapper_connection_is_set_none_arg(self):
        a_input = 123
        a, connection = connection_test(a_input, None)
        self.assertIsNotNone(connection)
        self.assertEqual(a_input, a)


@DefaultConnection
def connection_test(a=None, connection=None):
    return a, connection


class ExtractKeysCommand(TestCase):
    def test_command_output(self):
        out = StringIO()
        call_command("extract_keys", file="local_push.p12", password="bazinga", stdout=out)
        out_getvalue = out.getvalue()
        self.assertIn('SCARFACE_APNS_CERTIFICATE', out_getvalue)