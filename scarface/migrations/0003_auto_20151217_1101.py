# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scarface', '0002_auto_20151217_1017'),
    ]

    operations = [
        migrations.AlterField(
            model_name='platform',
            name='platform',
            field=models.CharField(max_length=255),
        ),
    ]
