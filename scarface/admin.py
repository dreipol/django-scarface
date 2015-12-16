# -*- coding: utf-8 -*-
from django.contrib import admin
from scarface.models import Application, Platform, Topic, PushMessage

__author__ = 'janmeier'

class PlatformInline(admin.TabularInline):
    model = Platform
    extra = 0


class ApplicationAdmin(admin.ModelAdmin):
    inlines = [PlatformInline]
    list_display = ['name']


class PlatformAdmin(admin.ModelAdmin):
    list_display = ['platform', 'application', 'arn']


class TopicAdmin(admin.ModelAdmin):
    list_display = ['name', 'application', 'arn']


admin.site.register(Application, ApplicationAdmin)
admin.site.register(Platform, PlatformAdmin)
admin.site.register(Topic, TopicAdmin)
admin.site.register(PushMessage)
