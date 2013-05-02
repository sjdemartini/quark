# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'PiEEvent'
        db.create_table(u'pie_events_pieevent', (
            (u'event_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['events.Event'], unique=True, primary_key=True)),
            ('season', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base_pie.Season'])),
        ))
        db.send_create_signal(u'pie_events', ['PiEEvent'])


    def backwards(self, orm):
        # Deleting model 'PiEEvent'
        db.delete_table(u'pie_events_pieevent')


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
        u'base_pie.season': {
            'Meta': {'object_name': 'Season'},
            'end_date': ('django.db.models.fields.DateField', [], {}),
            'start_date': ('django.db.models.fields.DateField', [], {}),
            'year': ('django.db.models.fields.PositiveIntegerField', [], {'primary_key': 'True'})
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
        },
        u'events.event': {
            'Meta': {'ordering': "('start_datetime',)", 'object_name': 'Event'},
            'cancelled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'committee': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['base_tbp.OfficerPosition']"}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'end_datetime': ('django.db.models.fields.DateTimeField', [], {}),
            'event_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['events.EventType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'max_guests_per_person': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'needs_drivers': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'project_report': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'event'", 'null': 'True', 'blank': 'True', 'to': u"orm['project_reports.ProjectReport']"}),
            'requirements_credit': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'signup_limit': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'start_datetime': ('django.db.models.fields.DateTimeField', [], {}),
            'tagline': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'term': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['base.Term']"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'events.eventtype': {
            'Meta': {'object_name': 'EventType'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'})
        },
        u'pie_events.pieevent': {
            'Meta': {'ordering': "('start_datetime',)", 'object_name': 'PiEEvent', '_ormbases': [u'events.Event']},
            u'event_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['events.Event']", 'unique': 'True', 'primary_key': 'True'}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['base_pie.Season']"})
        },
        u'project_reports.projectreport': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'ProjectReport'},
            'area': ('django.db.models.fields.CharField', [], {'max_length': '2', 'blank': 'True'}),
            'attachment': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'blank': 'True'}),
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'candidate_list': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'candidate_list+'", 'blank': 'True', 'to': u"orm['auth.User']"}),
            'committee': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['base_tbp.OfficerPosition']"}),
            'complete': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'cost': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'first_completed_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_new': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'member_list': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'member_list+'", 'blank': 'True', 'to': u"orm['auth.User']"}),
            'non_tbp': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'officer_list': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'officer_list+'", 'blank': 'True', 'to': u"orm['auth.User']"}),
            'organization': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'organize_hours': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'other_group': ('django.db.models.fields.CharField', [], {'max_length': '60', 'blank': 'True'}),
            'participate_hours': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'problems': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'purpose': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'results': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'term': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['base.Term']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['pie_events']