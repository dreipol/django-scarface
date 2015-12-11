# -*- coding: utf-8 -*-
__author__ = 'janmeier'

class SNSNotCreatedException(Exception):
    message = "Register the instance before deleting it by calling register()"

class PlatformNotSupported(Exception):
    message = ""


