# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Vendor'
        db.create_table(u'pie_staff_purchase_vendor', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'pie_staff_purchase', ['Vendor'])

        # Adding model 'PartsReceipt'
        db.create_table(u'pie_staff_purchase_partsreceipt', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('confirmation_number', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('receipt', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('total_cost', self.gf('django.db.models.fields.DecimalField')(max_digits=8, decimal_places=2)),
            ('tracking_number', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('vendor', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['pie_staff_purchase.Vendor'])),
            ('purchaser', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'pie_staff_purchase', ['PartsReceipt'])

        # Adding model 'PartOrder'
        db.create_table(u'pie_staff_purchase_partorder', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['pie_inventory.Item'])),
            ('quantity', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('unit_price', self.gf('django.db.models.fields.DecimalField')(max_digits=6, decimal_places=2)),
            ('vendor', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['pie_staff_purchase.Vendor'])),
            ('vendor_part_num', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('vendor_link', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('order', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['pie_staff_purchase.PartsReceipt'], null=True)),
            ('notes', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('purchase_category', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('submitted_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'pie_staff_purchase', ['PartOrder'])

        # Adding model 'PartOrderStatus'
        db.create_table(u'pie_staff_purchase_partorderstatus', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('comments', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('part', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['pie_staff_purchase.PartOrder'])),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'pie_staff_purchase', ['PartOrderStatus'])


    def backwards(self, orm):
        # Deleting model 'Vendor'
        db.delete_table(u'pie_staff_purchase_vendor')

        # Deleting model 'PartsReceipt'
        db.delete_table(u'pie_staff_purchase_partsreceipt')

        # Deleting model 'PartOrder'
        db.delete_table(u'pie_staff_purchase_partorder')

        # Deleting model 'PartOrderStatus'
        db.delete_table(u'pie_staff_purchase_partorderstatus')


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
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'pie_inventory.item': {
            'Meta': {'object_name': 'Item'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'picture': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'wiki': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        u'pie_staff_purchase.partorder': {
            'Meta': {'object_name': 'PartOrder'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pie_inventory.Item']"}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pie_staff_purchase.PartsReceipt']", 'null': 'True'}),
            'purchase_category': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'quantity': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'submitted_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'unit_price': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '2'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'vendor': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pie_staff_purchase.Vendor']"}),
            'vendor_link': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'vendor_part_num': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        u'pie_staff_purchase.partorderstatus': {
            'Meta': {'object_name': 'PartOrderStatus'},
            'comments': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'part': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pie_staff_purchase.PartOrder']"}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'pie_staff_purchase.partsreceipt': {
            'Meta': {'object_name': 'PartsReceipt'},
            'confirmation_number': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'purchaser': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'receipt': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'total_cost': ('django.db.models.fields.DecimalField', [], {'max_digits': '8', 'decimal_places': '2'}),
            'tracking_number': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'vendor': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pie_staff_purchase.Vendor']"})
        },
        u'pie_staff_purchase.vendor': {
            'Meta': {'object_name': 'Vendor'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['pie_staff_purchase']