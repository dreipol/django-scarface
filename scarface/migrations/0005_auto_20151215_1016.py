# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scarface', '0004_auto_20151211_1424'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='topics',
            field=models.ManyToManyField(through='scarface.Subscription', to='scarface.Topic'),
        ),
        migrations.AlterField(
            model_name='platform',
            name='platform',
            field=models.CharField(choices=[('GCM', 'Google Cloud Messaging (GCM)'), ('APNS', 'Apple Push Notification Service (APNS)'), ('APNS_SANDBOX', 'Apple Push Notification Service Sandbox (APNS_SANDBOX)')], max_length=255),
        ),
    ]
