# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scarface', '0003_auto_20151211_1424'),
    ]

    operations = [
        migrations.AddField(
            model_name='topic',
            name='devices',
            field=models.ManyToManyField(to='scarface.Device', through='scarface.Subscription'),
        ),
        migrations.AlterField(
            model_name='platform',
            name='platform',
            field=models.CharField(choices=[('APNS_SANDBOX', 'Apple Push Notification Service Sandbox (APNS_SANDBOX)'), ('GCM', 'Google Cloud Messaging (GCM)'), ('APNS', 'Apple Push Notification Service (APNS)')], max_length=255),
        ),
    ]
