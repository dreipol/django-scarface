# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PushMessage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sound', models.TextField(null=True, blank=True)),
                ('message', models.TextField(default=b'', null=True)),
                ('has_new_content', models.BooleanField(default=False)),
                ('context_id', models.TextField(default=b'none', null=True)),
                ('context', models.TextField(default=b'default', null=True)),
                ('badge_count', models.SmallIntegerField(default=0)),
                ('extra_payload', models.TextField(null=True, blank=True)),
                ('receiver_arn', models.TextField(null=True, blank=True)),
                ('message_type', models.PositiveSmallIntegerField(default=0)),
            ],
        ),
    ]