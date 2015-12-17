# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def set_platform(apps, schema_editor):
    Device = apps.get_model('scarface', 'Device')
    for device in Device.objects.all():
        device.platform = device.application.get_platform(device)
        device.save()

class Migration(migrations.Migration):

    dependencies = [
        ('scarface', '0002_auto_20151216_1636'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='platform',
            field=models.ForeignKey(default=1, related_name='devices', to='scarface.Platform'),
            preserve_default=False,
        ),
        migrations.RunPython(set_platform),
        migrations.AlterUniqueTogether(
            name='device',
            unique_together=set([('device_id', 'platform')]),
        ),
    ]
