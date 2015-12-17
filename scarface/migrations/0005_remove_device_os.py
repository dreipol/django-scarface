# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scarface', '0004_remove_device_application'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='device',
            name='os',
        ),
    ]
