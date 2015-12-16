# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scarface', '0002_auto_20151215_1633'),
    ]

    operations = [
        migrations.AlterField(
            model_name='platform',
            name='platform',
            field=models.CharField(choices=[('APNS', 'Apple Push Notification Service (APNS)'), ('APNS_SANDBOX', 'Apple Push Notification Service Sandbox (APNS_SANDBOX)'), ('GCM', 'Google Cloud Messaging (GCM)')], max_length=255),
        ),
    ]
