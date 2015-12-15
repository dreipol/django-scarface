# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import scarface.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('device_id', models.CharField(max_length=255)),
                ('arn', models.CharField(max_length=255, null=True, blank=True)),
                ('push_token', models.CharField(max_length=255)),
                ('os', models.SmallIntegerField(choices=[(1, 'iOS'), (2, 'Android')])),
                ('application', models.ForeignKey(on_delete=None, to='scarface.Application', related_name='devices')),
            ],
            bases=(scarface.models.SNSCRUDMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Platform',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('platform', models.CharField(max_length=255, choices=[('APNS_SANDBOX', 'Apple Push Notification Service Sandbox (APNS_SANDBOX)'), ('APNS', 'Apple Push Notification Service (APNS)'), ('GCM', 'Google Cloud Messaging (GCM)')])),
                ('arn', models.CharField(max_length=255, null=True, blank=True)),
                ('credential', models.CharField(max_length=255, null=True, blank=True)),
                ('principal', models.CharField(max_length=255, null=True, blank=True)),
                ('application', models.ForeignKey(on_delete=None, to='scarface.Application', related_name='platforms')),
            ],
            bases=(scarface.models.SNSCRUDMixin, models.Model),
        ),
        migrations.CreateModel(
            name='PushMessage',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('sound', models.TextField(null=True, blank=True)),
                ('message', models.TextField(null=True, default='')),
                ('has_new_content', models.BooleanField(default=False)),
                ('context_id', models.TextField(null=True, default='none')),
                ('context', models.TextField(null=True, default='default')),
                ('badge_count', models.SmallIntegerField(default=0)),
                ('extra_payload', models.TextField(null=True, blank=True)),
                ('receiver_arn', models.TextField(null=True, blank=True)),
                ('message_type', models.PositiveSmallIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('arn', models.CharField(max_length=255, null=True, blank=True)),
                ('device', models.ForeignKey(to='scarface.Device')),
            ],
            bases=(scarface.models.SNSCRUDMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=64)),
                ('arn', models.CharField(max_length=255, null=True, blank=True)),
                ('application', models.ForeignKey(to='scarface.Application', related_name='topics')),
                ('devices', models.ManyToManyField(through='scarface.Subscription', to='scarface.Device')),
            ],
            bases=(scarface.models.SNSCRUDMixin, models.Model),
        ),
        migrations.AddField(
            model_name='subscription',
            name='topic',
            field=models.ForeignKey(to='scarface.Topic'),
        ),
        migrations.AddField(
            model_name='device',
            name='topics',
            field=models.ManyToManyField(through='scarface.Subscription', to='scarface.Topic'),
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
            unique_together=set([('device_id', 'application')]),
        ),
    ]
