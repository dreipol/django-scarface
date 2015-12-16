# -*- coding: utf-8 -*-
from django.apps import AppConfig as BaseAppConfig
__author__ = 'janmeier'

class AppConfig(BaseAppConfig):
    name = 'scarface'
    verbose_name ='Scarface'

    def ready(self):
        from . import signals
