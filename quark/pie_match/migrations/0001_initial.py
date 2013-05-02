# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Alliance'
        db.create_table(u'pie_match_alliance', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('autonomous', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('bonus', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('manual', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('penalty', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'pie_match', ['Alliance'])

        # Adding model 'AllianceMember'
        db.create_table(u'pie_match_alliancemember', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('alliance', self.gf('django.db.models.fields.related.ForeignKey')(related_name='alliance_member', to=orm['pie_match.Alliance'])),
            ('disqualified', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('team', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['base_pie.Team'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'pie_match', ['AllianceMember'])

        # Adding model 'Match'
        db.create_table(u'pie_match_match', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('blue', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['pie_match.Alliance'])),
            ('completed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('description', self.gf('django.db.models.fields.TextField')(default='Match')),
            ('final', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('gold', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['pie_match.Alliance'])),
            ('match_time', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 10, 31, 0, 0))),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'pie_match', ['Match'])


    def backwards(self, orm):
        # Deleting model 'Alliance'
        db.delete_table(u'pie_match_alliance')

        # Deleting model 'AllianceMember'
        db.delete_table(u'pie_match_alliancemember')

        # Deleting model 'Match'
        db.delete_table(u'pie_match_match')


    models = {
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
        u'pie_match.alliance': {
            'Meta': {'object_name': 'Alliance'},
            'autonomous': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'bonus': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'manual': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'penalty': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'pie_match.alliancemember': {
            'Meta': {'object_name': 'AllianceMember'},
            'alliance': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'alliance_member'", 'to': u"orm['pie_match.Alliance']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'disqualified': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['base_pie.Team']"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'pie_match.match': {
            'Meta': {'object_name': 'Match'},
            'blue': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['pie_match.Alliance']"}),
            'completed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "'Match'"}),
            'final': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'gold': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['pie_match.Alliance']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'match_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 31, 0, 0)'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['pie_match']