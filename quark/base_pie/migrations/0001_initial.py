# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Season'
        db.create_table(u'base_pie_season', (
            ('year', self.gf('django.db.models.fields.PositiveIntegerField')(primary_key=True)),
            ('start_date', self.gf('django.db.models.fields.DateField')()),
            ('end_date', self.gf('django.db.models.fields.DateField')()),
        ))
        db.send_create_signal(u'base_pie', ['Season'])

        # Adding model 'School'
        db.create_table(u'base_pie_school', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200)),
            ('street_number', self.gf('django.db.models.fields.IntegerField')()),
            ('street', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('state', self.gf('django_localflavor_us.models.USStateField')(max_length=2)),
            ('zipcode', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'base_pie', ['School'])

        # Adding model 'Team'
        db.create_table(u'base_pie_team', (
            ('number', self.gf('django.db.models.fields.PositiveIntegerField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('school', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base_pie.School'])),
            ('season', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base_pie.Season'])),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('car_required', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('extra_attention', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('created', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'base_pie', ['Team'])

        # Adding unique constraint on 'Team', fields ['number', 'season']
        db.create_unique(u'base_pie_team', ['number', 'season_id'])

        # Adding model 'Teacher'
        db.create_table(u'base_pie_teacher', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('id_code', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('team', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base_pie.Team'])),
            ('created', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'base_pie', ['Teacher'])

        # Adding model 'Mentor'
        db.create_table(u'base_pie_mentor', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('id_code', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('team', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base_pie.Team'])),
            ('created', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'base_pie', ['Mentor'])

        # Adding model 'Student'
        db.create_table(u'base_pie_student', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('id_code', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('team', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base_pie.Team'])),
            ('leader', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('year_in_school', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('created', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'base_pie', ['Student'])


    def backwards(self, orm):
        # Removing unique constraint on 'Team', fields ['number', 'season']
        db.delete_unique(u'base_pie_team', ['number', 'season_id'])

        # Deleting model 'Season'
        db.delete_table(u'base_pie_season')

        # Deleting model 'School'
        db.delete_table(u'base_pie_school')

        # Deleting model 'Team'
        db.delete_table(u'base_pie_team')

        # Deleting model 'Teacher'
        db.delete_table(u'base_pie_teacher')

        # Deleting model 'Mentor'
        db.delete_table(u'base_pie_mentor')

        # Deleting model 'Student'
        db.delete_table(u'base_pie_student')


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
        u'base_pie.mentor': {
            'Meta': {'object_name': 'Mentor'},
            'created': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'id_code': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['base_pie.Team']"}),
            'updated': ('django.db.models.fields.DateField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'base_pie.school': {
            'Meta': {'ordering': "('name',)", 'object_name': 'School'},
            'city': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'state': ('django_localflavor_us.models.USStateField', [], {'max_length': '2'}),
            'street': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'street_number': ('django.db.models.fields.IntegerField', [], {}),
            'zipcode': ('django.db.models.fields.IntegerField', [], {})
        },
        u'base_pie.season': {
            'Meta': {'object_name': 'Season'},
            'end_date': ('django.db.models.fields.DateField', [], {}),
            'start_date': ('django.db.models.fields.DateField', [], {}),
            'year': ('django.db.models.fields.PositiveIntegerField', [], {'primary_key': 'True'})
        },
        u'base_pie.student': {
            'Meta': {'object_name': 'Student'},
            'created': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'id_code': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'leader': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['base_pie.Team']"}),
            'updated': ('django.db.models.fields.DateField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'year_in_school': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        },
        u'base_pie.teacher': {
            'Meta': {'object_name': 'Teacher'},
            'created': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'id_code': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['base_pie.Team']"}),
            'updated': ('django.db.models.fields.DateField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'base_pie.team': {
            'Meta': {'ordering': "('number',)", 'unique_together': "(('number', 'season'),)", 'object_name': 'Team'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'car_required': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'extra_attention': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'number': ('django.db.models.fields.PositiveIntegerField', [], {'primary_key': 'True'}),
            'school': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['base_pie.School']"}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['base_pie.Season']"}),
            'updated': ('django.db.models.fields.DateField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['base_pie']