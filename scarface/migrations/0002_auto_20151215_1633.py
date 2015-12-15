# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scarface', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='device',
            name='application',
            field=models.ForeignKey(related_name='devices', to='scarface.Application'),
        ),
        migrations.AlterField(
            model_name='platform',
            name='application',
            field=models.ForeignKey(related_name='platforms', to='scarface.Application'),
        ),
    ]
