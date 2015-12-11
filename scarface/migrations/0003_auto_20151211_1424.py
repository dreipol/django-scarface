# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import scarface.models


class Migration(migrations.Migration):

    dependencies = [
        ('scarface', '0002_auto_20151210_1506'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('arn', models.CharField(null=True, blank=True, max_length=255)),
                ('device', models.ForeignKey(to='scarface.Device')),
                ('topic', models.ForeignKey(to='scarface.Topic')),
            ],
            bases=(scarface.models.SNSCRUDMixin, models.Model),
        ),
        migrations.AlterField(
            model_name='platform',
            name='platform',
            field=models.CharField(choices=[('GCM', 'Google Cloud Messaging (GCM)'), ('APNS', 'Apple Push Notification Service (APNS)'), ('APNS_SANDBOX', 'Apple Push Notification Service Sandbox (APNS_SANDBOX)')], max_length=255),
        ),
        migrations.AlterUniqueTogether(
            name='subscription',
            unique_together=set([('topic', 'device')]),
        ),
    ]
