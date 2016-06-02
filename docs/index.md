![django-scarface](logo_transparent.png)

# Welcome to django-scarface

Send push notifications to mobile devices using Amazon SNS.

## Getting Started

### Installation

You can install Scarface directly from pypi using pip:
```zsh
pip install django-scarface
```


Edit your settings.py file:

```python
INSTALLED_APPS = (
    ...
    "scarface",
)
```

## Settings

| Name | Description | Mandatory | Default |
|------|-------------|-----------|---------|
| ``AWS_ACCESS_KEY`` | Acess key of your AWS user*. | Yes | - |
| ``AWS_SECRET_ACCESS_KEY`` | Secret key of your AWS user. | Yes | - |
| ``SCARFACE_LOGGING_ENABLED`` | If true the push messages are logged to the DB.| | ``True`` |
| ``SCARFACE_PLATFORM_STRATEGIES`` | A list of [additional platform strategies](#register-new-platforms) to integrate other AWS platforms.| No | `[]`|
| ``SCARFACE_MESSAGE_TRIM_LENGTH`` | The length of a push notification, defaults to 140 chars. Please note that there are platform specific restrictions.| No | `140`|
**We assume that user has all the privileges to create Applications, Endpoints and Topics *


## Management Commands
### extract_keys
You can extract the SCARFACE_APNS_CERTIFICATE and SCARFACE_APNS_PRIVATE_KEY settings from a .p12 file exported from Keychain Access. The usage is as simple as the following example:
```bash
python manage.py extract_keys --file=Certificate.p12 --password=<MYPASSWORD>
```
The output can be copied and pasted into your settings file.

## Usage
The code it self is good documented. You may also check the unittests (`tests.py`) or implementation details.

## Tutorial
This is a tutorial how you create AWS Applications, Platforms etc. programmatically. Alternatively you can create the modeinstances in the django admin area.

### Create Applications and Platforms
First you have to create a new application.
```python
app = Application.objects.create(name='test_application)
```

### Create Platforms
Once you have successfully created an application you can add platforms to that
it. Currently only 'Google Cloud Messaging' and 'Apple Push Notification
Service' are available. If you wish, you can [add further strategies](#register-new-platforms) to support
more platforms.
```python
apns_platform = Platform.objects.create(
    platform='APNS',
    application=app,
    arn=TEST_ARN_TOKEN_APNS
)

gcm_platform = Platform.objects.create(
    platform='GCM',
    application=app,
    arn=TEST_ARN_TOKEN_APNS
)
```
The available values for the platform parameter are:

| Value | Name |
|-------|------|
| ``GCM`` | Google Cloud Messaging |
| ``APNS`` | Apple Push Notification Service |
| ``APNS_SANDBOX`` | Apple Push Notification Service Sandbox |

### Create Platforms
Having a setup platform you are now ready to register new devices to that platform.
```python
apple_device = Device.objects.create(
    device_id=<device_id>,
    push_token=<device_push_token>,
    platform=apns_platform
)
andorid_device = Device.objects.create(
    device_id=<device_id>,
    push_token=<device_push_token>,
    platform=gcm_platform
)

apple_device.register()
android_device.register()
```

### Create Topics
Before you can subscribe a device to a topic we have to create that topic.
```python
topic = Topic.objects.create(
    name='test_topic',
    application = app,
)

topic.register()
```

### Subscribe to Topic
Once the platforms, devices and topics have been set up you can register the devices to topics.
```python
topic.register_device(arn_device)
```

###  Deregsiter
All the above mentioned classes which support the ``register()`` method can be deregistered by using their ``deregister()`` method. Further, when you delete them, they automatically deregister.


### Send Push Notifications

Register a device like seen above.

Send a push message:
```python
message = PushMessage(
    badge_count=1,
    context='url_alert',
    context_id='none',
    has_new_content=True,
    message="Hello world!",
    sound="default"
)
ios_device.send(message)
```

If logging is enabled, all sent push messages are logged in the table scarface_pushmessage.



## Register New Platforms
If you want to register a new platform create a new subclass of the abstract ``PlatformStrategy`` class. Take a look on an existin implementation for an example.

Then add it to the ``SCARFACE_PLATFORM_STRATEGIES`` settings parameter:
```
SCARFACE_PLATFORM_STRATEGIES = [
    'path.to.my.PlatformStrategy'
]
```
By giving you own class the same ID as the one of an existing implementation, you overwrite that implementation.


## FAQ

_How do I change the credentials?_

There is no direct way yet to exchange the credentials. To exchange the API credentials you'll have to replace the old one in the settings file and in the AWS console manually.

Now have fun using this library and [push it to the limit](https://www.youtube.com/watch?v=9D-QD_HIfjA).

![the movie](scarface-movie.png)
