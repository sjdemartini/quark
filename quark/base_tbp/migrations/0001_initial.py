# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'OfficerPosition'
        db.create_table(u'base_tbp_officerposition', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('position_type', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('short_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=16)),
            ('long_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64)),
            ('rank', self.gf('django.db.models.fields.DecimalField')(max_digits=5, decimal_places=2)),
            ('mailing_list', self.gf('django.db.models.fields.CharField')(max_length=16, blank=True)),
        ))
        db.send_create_signal(u'base_tbp', ['OfficerPosition'])

        # Adding model 'Officer'
        db.create_table(u'base_tbp_officer', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('position', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base_tbp.OfficerPosition'])),
            ('term', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.Term'])),
            ('is_chair', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'base_tbp', ['Officer'])

        # Adding unique constraint on 'Officer', fields ['user', 'position', 'term']
        db.create_unique(u'base_tbp_officer', ['user_id', 'position_id', 'term_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Officer', fields ['user', 'position', 'term']
        db.delete_unique(u'base_tbp_officer', ['user_id', 'position_id', 'term_id'])

        # Deleting model 'OfficerPosition'
        db.delete_table(u'base_tbp_officerposition')

        # Deleting model 'Officer'
        db.delete_table(u'base_tbp_officer')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'base.term': {
            'Meta': {'ordering': "('id',)", 'unique_together': "(('term', 'year'),)", 'object_name': 'Term'},
            'current': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'term': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'year': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        },
        u'base_tbp.officer': {
            'Meta': {'unique_together': "(('user', 'position', 'term'),)", 'object_name': 'Officer'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_chair': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'position': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['base_tbp.OfficerPosition']"}),
            'term': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['base.Term']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'base_tbp.officerposition': {
            'Meta': {'ordering': "('rank',)", 'object_name': 'OfficerPosition'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'long_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'mailing_list': ('django.db.models.fields.CharField', [], {'max_length': '16', 'blank': 'True'}),
            'position_type': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'rank': ('django.db.models.fields.DecimalField', [], {'max_digits': '5', 'decimal_places': '2'}),
            'short_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '16'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['base_tbp']