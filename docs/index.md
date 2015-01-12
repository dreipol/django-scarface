![django-scarface](logo_transparent.png)

# Welcome to django-scarface

Send push notifications to mobile devices using Amazon SNS.

## Getting Started

### Setup
You can install Scarface directly from pypi using pip::

	$ pip install django-scarface


Edit your settings.py file::

	INSTALLED_APPS = (
		...
		"scarface",
	)


Native Django migrations are supported on Django 1.7 and beyond. The app will automatically
fall back to South on older versions, however you will also need the following setting::

	SOUTH_MIGRATION_MODULES = {"scarface": "scarface.migrations"}

Add your AWS credentials and the required settings for Apple Push Notifications and/or Google Cloud Messaging as documented in the [Settings Chapter](#settings).


## Settings
The following settings are required:

The credentials of your AWS user. We expect the user to have all the priviliges to create Applications, Endpoints and Topics

    AWS_ACCESS_KEY = "<YOUR_AWS_ACCESS_KEY>"
    AWS_SECRET_ACCESS_KEY = "<YOUR_AWS_SECRET_ACCESS_KEY>"

The mode for Apple Push Notifications. Either "APNS" for production or "APNS_SANDBOX" for the sandbox environment.

    SCARFACE_APNS_MODE = u"APNS_SANDBOX"

The name of the application that will be created. This name is later postfixed with the platform, for example the Application name will be 'Scarface_Test_gcm' or 'Scarface_Test_apns'

    SCARFACE_SNS_APP_PREFIX = u"Scarface_Test"

Your Google Cloud Messaging Key. It is expected to be a Server-Key

    SCARFACE_GCM_API_KEY = "<YOUR-GCM-API-KEY>"

The APNS certificate and private key as a string. you can create this settings by using the "manage.py extract_keys" command and a P12 file.

    SCARFACE_APNS_CERTIFICATE = "<YOUR-APNS-CERTIFICATE-KEY>"
    SCARFACE_APNS_PRIVATE_KEY = "<YOUR-APNS-PRIVATE-KEY>"

Enable/Disable Push message logging 
    
    SCARFACE_LOGGING_ENABLED = True (Default)

## Management Commands
### extract_keys
You can extract the SCARFACE_APNS_CERTIFICATE and SCARFACE_APNS_PRIVATE_KEY settings from a .p12 file exported from Keychain Access. The usage is as simple as the following example:

    python manage.py extract_keys --file=Certificate.p12 --password=<MYPASSWORD>

The output can be copied and pasted into your settings file.

## Usage
The code it self is good documented. You may also check the unittests (`tests.py`) or implementation details.

### Devices Registration
Create and register the app:
    
    apn_app = APNApplication()
    apn_app.register()

Create and register the device:

    push_token = "<iOS PushToken>"
    ios_device = SNSDevice(apn_app, push_token)
    ios_device.register_or_update()

For GCM it's the same approach. Just create an `GCMApplication`.

    

### Send Push Notifications

Register a device like seen above.

Send a push message:

    message = PushMessage(badge_count=1, context='url_alert', context_id='none',
                        has_new_content=True, message="Hello world!", sound="default")
    ios_device.send(message)

If logging is enabled, all sent push messages are logged in the table scarface_pushmessage.


## Examples

### Registration
    def register(your_device_instance, token):
        from scarface.models import SNSDevice, APNApplication, GCMApplication

        """
        registers the device to sns
        :param your_device_instance: the device
        :param token: the push token or the registration id
        """

        # get the correct notification plattform
        if your_device_instance.is_ios():
            application_plattform = APNApplication()
        else:
            application_plattform = GCMApplication()

        #register the application
        application_plattform.register()

        # create the device resource with the token (may be the push token or the registration id)
        sns_device = SNSDevice(application_plattform, token)

        # register the device with sns or update the token/the attributes
        sns_device.register_or_update(new_token=token, custom_user_data="customer_name={0}".format(your_device_instance.customer_name))

        # this is importat: after updating or registration, your sns resource should have a arn. save this to your database.
        if sns_device.arn:
            your_device_instance.arn = sns_device.arn
            your_device_instance.save()

### Send Push Notifications
    def push(message, badge, targeted_devices):
        from scarface.models import SNSDevice, APNApplication, GCMApplication, PushMessage
        """
        sends a push to the targeted devices
        :param message: the text message
        :param badge: the new badge count (only applies to ios
        """


        # set up the application. in this scenario we can target both platforms
        apns = APNApplication()
        gcm = GCMApplication()

        # for every targeted device...
        for your_device_instance in targeted_devices:
            # ...get the correct application
            if your_device_instance.is_ios():
                application_platform = apns
            else:
                application_platform = gcm

            # and if your device model has a arn....
            if your_device_instance.arn:

                # ...create the device resource...
                sns_device = SNSDevice(application_platform, your_device_instance.push_token, arn=your_device_instance.arn)
                # ... and the push message...
                message = PushMessage(badge_count=badge, context='push', context_id='none', has_new_content=True,
                                      message=message, sound="default")
                # ...and then send it.
                sns_device.send(message)

##FAQ

_How do I change the credentials?_

There is no direct way yet to exchange the credentials. To exchange the API credentials you'll have to replace the old one in the settings file and in the AWS console manually. 

Now have fun using this library and [push it to the limit](https://www.youtube.com/watch?v=9D-QD_HIfjA).

![the movie](scarface-movie.png)