# -*- coding: utf-8 -*-
from django.contrib import admin

from scarface.models import Application, Platform

__author__ = 'janmeier'

class PlatformInline(admin.TabularInline):
    model = Platform

class ApplicationAdmin(admin.ModelAdmin):
    inlines = [PlatformInline]

admin.site.register(Application)
admin.site.register(Platform)