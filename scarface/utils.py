# -*- coding: utf-8 -*-
from functools import partial
import inspect
from boto import sns
from django.conf import settings

__author__ = 'dreipol GmbH'


class Decorator(object):
    def __init__(self, function, *args, **kwargs):
        self.function = function

    @property
    def original_function(self):
        function = self.function
        while isinstance(function, Decorator):
            function = function.function
        return function


class DefaultConnection(Decorator):
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self.function
        return partial(self, obj)

    def __call__(self, *args, **kwargs):
        connection_keyword = 'connection'
        if len(args) + len(kwargs) == 0:
            call_kwargs = dict()
        else:
            call_kwargs = inspect.getcallargs(
                self.original_function,
                *args,
                **kwargs
            )
        if not call_kwargs.get(connection_keyword, None):
            call_kwargs[connection_keyword] = get_sns_connection()
        return self.function(**call_kwargs)


class PushLogger(Decorator):
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self.function
        self.obj = obj
        return partial(self, obj)

    def __call__(self, *args, **kwargs):
        call_kwargs = inspect.getcallargs(self.original_function, *args,
                                          **kwargs)
        push_message = call_kwargs.get('push_message')
        self.obj.sign(push_message)
        if logging_enabled():
            push_message.save()
        return self.function(*args, **kwargs)


def get_sns_connection(region='eu-west-1'):
    """
    Creates a new AWS connection based upon the credentials defined in the django configuration
    :param region: the region of the DynamoDB, defaults to Ireland
    :return: a new dynamodb2 connection
    """

    return sns.connect_to_region(
        region, aws_access_key_id=settings.AWS_ACCESS_KEY,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )


def logging_enabled():
    return settings.SCARFACE_LOGGING_ENABLED if hasattr(
        settings,
        'SCARFACE_LOGGING_ENABLED'
    ) else True