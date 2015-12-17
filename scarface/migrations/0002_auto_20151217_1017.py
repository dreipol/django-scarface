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
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('device_id', models.CharField(max_length=255)),
                ('arn', models.CharField(null=True, max_length=255, blank=True)),
                ('push_token', models.CharField(max_length=255)),
            ],
            bases=(scarface.models.SNSCRUDMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Platform',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('platform', models.CharField(choices=[('APNS', 'Apple Push Notification Service (APNS)'), ('APNS_SANDBOX', 'Apple Push Notification Service Sandbox (APNS_SANDBOX)'), ('GCM', 'Google Cloud Messaging (GCM)')], max_length=255)),
                ('arn', models.CharField(null=True, max_length=255, blank=True)),
                ('credential', models.CharField(null=True, max_length=255, blank=True)),
                ('principal', models.CharField(null=True, max_length=255, blank=True)),
                ('application', models.ForeignKey(to='scarface.Application', related_name='platforms')),
            ],
            bases=(scarface.models.SNSCRUDMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('arn', models.CharField(null=True, max_length=255, blank=True)),
                ('device', models.ForeignKey(to='scarface.Device')),
            ],
            bases=(scarface.models.SNSCRUDMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('name', models.CharField(max_length=64)),
                ('arn', models.CharField(null=True, max_length=255, blank=True)),
                ('application', models.ForeignKey(to='scarface.Application', related_name='topics')),
                ('devices', models.ManyToManyField(to='scarface.Device', through='scarface.Subscription')),
            ],
            bases=(scarface.models.SNSCRUDMixin, models.Model),
        ),
        migrations.AlterField(
            model_name='pushmessage',
            name='context',
            field=models.TextField(null=True, default='default'),
        ),
        migrations.AlterField(
            model_name='pushmessage',
            name='context_id',
            field=models.TextField(null=True, default='none'),
        ),
        migrations.AlterField(
            model_name='pushmessage',
            name='message',
            field=models.TextField(null=True, default=''),
        ),
        migrations.AddField(
            model_name='subscription',
            name='topic',
            field=models.ForeignKey(to='scarface.Topic'),
        ),
        migrations.AddField(
            model_name='device',
            name='platform',
            field=models.ForeignKey(to='scarface.Platform', related_name='devices'),
        ),
        migrations.AddField(
            model_name='device',
            name='topics',
            field=models.ManyToManyField(to='scarface.Topic', through='scarface.Subscription'),
        ),
        migrations.AlterUniqueTogether(
            name='topic',
            unique_together=set([('name', 'application')]),
        ),
        migrations.AlterUniqueTogether(
            name='subscription',
            unique_together=set([('topic', 'device')]),
        ),
        migrations.AlterUniqueTogether(
            name='platform',
            unique_together=set([('application', 'platform')]),
        ),
        migrations.AlterUniqueTogether(
            name='device',
            unique_together=set([('device_id', 'platform')]),
        ),
    ]
