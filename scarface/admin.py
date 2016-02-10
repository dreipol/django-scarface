# -*- coding: utf-8 -*-
from django.contrib import admin

from scarface.forms import PlatformAdminForm
from scarface.models import Application, Platform, Topic, PushMessage, Device

__author__ = 'janmeier'

class PlatformInline(admin.TabularInline):
    model = Platform
    extra = 0
    form = PlatformAdminForm

class ApplicationAdmin(admin.ModelAdmin):
    inlines = [PlatformInline]
    list_display = ['name']


class PlatformAdmin(admin.ModelAdmin):
    list_display = ['platform', 'application', 'arn']
    exclude = ['credential', 'principal']
    form = PlatformAdminForm


class TopicAdmin(admin.ModelAdmin):
    list_display = ['name', 'application', 'arn']


class DeviceAdmin(admin.ModelAdmin):
    list_display = ['device_id', 'platform', 'arn', 'push_token']


admin.site.register(Application, ApplicationAdmin)
admin.site.register(Platform, PlatformAdmin)
admin.site.register(Topic, TopicAdmin)
admin.site.register(PushMessage)
admin.site.register(Device, DeviceAdmin)
