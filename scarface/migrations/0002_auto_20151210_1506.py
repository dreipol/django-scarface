# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import scarface.models


class Migration(migrations.Migration):

    dependencies = [
        ('scarface', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
            bases=(scarface.models.SNSCRUDMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('device_id', models.CharField(max_length=255)),
                ('arn', models.CharField(max_length=255, null=True, blank=True)),
                ('push_token', models.CharField(max_length=255)),
                ('os', models.SmallIntegerField(choices=[(1, 'iOS'), (2, 'Android')])),
                ('application', models.ForeignKey(to='scarface.Application', on_delete=None, related_name='devices')),
            ],
            bases=(scarface.models.SNSCRUDMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Platform',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('platform', models.CharField(max_length=255, choices=[('APNS', 'Apple Push Notification Service (APNS)'), ('APNS_SANDBOX', 'Apple Push Notification Service Sandbox (APNS_SANDBOX)'), ('GCM', 'Google Cloud Messaging (GCM)')])),
                ('arn', models.CharField(max_length=255, null=True, blank=True)),
                ('credential', models.CharField(max_length=255, null=True, blank=True)),
                ('principal', models.CharField(max_length=255, null=True, blank=True)),
                ('application', models.ForeignKey(to='scarface.Application', on_delete=None, related_name='platforms')),
            ],
            bases=(scarface.models.SNSCRUDMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=64)),
                ('arn', models.CharField(max_length=255, null=True, blank=True)),
                ('application', models.ForeignKey(to='scarface.Application', related_name='topics')),
            ],
            bases=(scarface.models.SNSCRUDMixin, models.Model),
        ),
        migrations.AlterField(
            model_name='pushmessage',
            name='context',
            field=models.TextField(default='default', null=True),
        ),
        migrations.AlterField(
            model_name='pushmessage',
            name='context_id',
            field=models.TextField(default='none', null=True),
        ),
        migrations.AlterField(
            model_name='pushmessage',
            name='message',
            field=models.TextField(default='', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='topic',
            unique_together=set([('name', 'application')]),
        ),
        migrations.AlterUniqueTogether(
            name='platform',
            unique_together=set([('application', 'platform')]),
        ),
        migrations.AlterUniqueTogether(
            name='device',
            unique_together=set([('device_id', 'application')]),
        ),
    ]
