django-scarface
===============

Send push notifications to mobile devices using Amazon SNS

Setup
-----
You can install Scarface directly from pypi using pip::

	$ pip install django-scarface


Edit your settings.py file::

	INSTALLED_APPS = (
		...
		"scarface",
	)


Native Django migrations are supported on Django 1.7 and beyond. The app will automatically
fall back to South on older versions, however you will also need the following setting::

	SOUTH_MIGRATION_MODULES = {"push_notifications": "push_notifications.south_migrations"}
	

Project Home
------------
https://github.com/dreipol/django-scarface

PyPi
------------
https://pypi.python.org/pypi/django-scarface