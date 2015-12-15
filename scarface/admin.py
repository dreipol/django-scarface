# -*- coding: utf-8 -*-
from django.contrib import admin

from scarface.models import Application, Platform

__author__ = 'janmeier'

class PlatformInline(admin.TabularInline):
    model = Platform

class ApplicationAdmin(admin.ModelAdmin):
    inlines = [PlatformInline]
    list_display = ['name', 'application', 'arn']

class PlatformAdmin(admin.ModelAdmin):
    list_display = ['platform', 'application', 'arn']

admin.site.register(Application)
admin.site.register(Platform)