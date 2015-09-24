# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'PushMessage'
        db.create_table(u'scarface_pushmessage', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sound', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('message', self.gf('django.db.models.fields.TextField')(default='')),
            ('has_new_content', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('context_id', self.gf('django.db.models.fields.TextField')(default='none')),
            ('context', self.gf('django.db.models.fields.TextField')(default='default')),
            ('badge_count', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
            ('extra_payload', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('receiver_arn', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('message_type', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0)),
        ))
        db.send_create_signal(u'scarface', ['PushMessage'])


    def backwards(self, orm):
        # Deleting model 'PushMessage'
        db.delete_table(u'scarface_pushmessage')


    models = {
        u'scarface.pushmessage': {
            'Meta': {'object_name': 'PushMessage'},
            'badge_count': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'context': ('django.db.models.fields.TextField', [], {'default': "'default'"}),
            'context_id': ('django.db.models.fields.TextField', [], {'default': "'none'"}),
            'extra_payload': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'has_new_content': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'message_type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'receiver_arn': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'sound': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['scarface']