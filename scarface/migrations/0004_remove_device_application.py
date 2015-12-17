# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scarface', '0003_auto_20151216_1659'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='device',
            name='application',
        ),
    ]
