# -*- coding: utf-8 -*-
__author__ = 'janmeier'

class BaseScarfaceException(Exception):
    pass
class SNSNotCreatedException(BaseScarfaceException):
    message = "Register the instance before deleting it by calling register()"

class PlatformNotSupported(BaseScarfaceException):
    message = ""

class SNSException(BaseScarfaceException):
    pass

class NotRegisteredException(BaseScarfaceException):
    pass



