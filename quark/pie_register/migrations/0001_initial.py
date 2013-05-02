# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'TeamRegistration'
        db.create_table(u'pie_register_teamregistration', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('applicant_email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('experience', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('heard', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('heard_other', self.gf('django.db.models.fields.CharField')(max_length=100, null=True)),
            ('parents_drive', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('phone_number', self.gf('django_localflavor_us.models.PhoneNumberField')(max_length=20)),
            ('school_name', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('student_roster', self.gf('django.db.models.fields.TextField')()),
            ('teacher_drive', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('teacher_email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('teacher_name', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('team_name', self.gf('django.db.models.fields.CharField')(max_length=40, blank=True)),
            ('tools', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('why_interested', self.gf('django.db.models.fields.TextField')()),
            ('work_area', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('possible_times', self.gf('django.db.models.fields.TextField')()),
            ('applicant', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True)),
            ('season', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base_pie.Season'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'pie_register', ['TeamRegistration'])


    def backwards(self, orm):
        # Deleting model 'TeamRegistration'
        db.delete_table(u'pie_register_teamregistration')


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
        u'base_pie.season': {
            'Meta': {'object_name': 'Season'},
            'end_date': ('django.db.models.fields.DateField', [], {}),
            'start_date': ('django.db.models.fields.DateField', [], {}),
            'year': ('django.db.models.fields.PositiveIntegerField', [], {'primary_key': 'True'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'pie_register.teamregistration': {
            'Meta': {'object_name': 'TeamRegistration'},
            'applicant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True'}),
            'applicant_email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'experience': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'heard': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'heard_other': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parents_drive': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'phone_number': ('django_localflavor_us.models.PhoneNumberField', [], {'max_length': '20'}),
            'possible_times': ('django.db.models.fields.TextField', [], {}),
            'school_name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['base_pie.Season']"}),
            'student_roster': ('django.db.models.fields.TextField', [], {}),
            'teacher_drive': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'teacher_email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'teacher_name': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'team_name': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'tools': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'why_interested': ('django.db.models.fields.TextField', [], {}),
            'work_area': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        }
    }

    complete_apps = ['pie_register']