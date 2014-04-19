# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'UserProfile'
        db.create_table(u'user_profiles_userprofile', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
            ('preferred_name', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=64, blank=True)),
            ('middle_name', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('birthday', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('gender', self.gf('django.db.models.fields.CharField')(max_length=1, blank=True)),
            ('picture', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
            ('alt_email', self.gf('django.db.models.fields.EmailField')(max_length=75, blank=True)),
            ('cell_phone', self.gf('localflavor.us.models.PhoneNumberField')(max_length=20, blank=True)),
            ('home_phone', self.gf('localflavor.us.models.PhoneNumberField')(max_length=20, blank=True)),
            ('receive_text', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('local_address1', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('local_address2', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('local_city', self.gf('django.db.models.fields.CharField')(max_length=128, blank=True)),
            ('local_state', self.gf('localflavor.us.models.USStateField')(max_length=2, blank=True)),
            ('local_zip', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True)),
            ('perm_address1', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('perm_address2', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('perm_city', self.gf('django.db.models.fields.CharField')(max_length=128, blank=True)),
            ('perm_state', self.gf('localflavor.us.models.USStateField')(default='CA', max_length=2, blank=True)),
            ('perm_zip', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True)),
            ('international_address', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'user_profiles', ['UserProfile'])

        # Adding model 'CollegeStudentInfo'
        db.create_table(u'user_profiles_collegestudentinfo', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('id_code', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
            ('start_term', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', null=True, to=orm['base.Term'])),
            ('grad_term', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', null=True, to=orm['base.Term'])),
        ))
        db.send_create_signal(u'user_profiles', ['CollegeStudentInfo'])

        # Adding M2M table for field major on 'CollegeStudentInfo'
        m2m_table_name = db.shorten_name(u'user_profiles_collegestudentinfo_major')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('collegestudentinfo', models.ForeignKey(orm[u'user_profiles.collegestudentinfo'], null=False)),
            ('major', models.ForeignKey(orm[u'base.major'], null=False))
        ))
        db.create_unique(m2m_table_name, ['collegestudentinfo_id', 'major_id'])

        # Adding model 'StudentOrgUserProfile'
        db.create_table(u'user_profiles_studentorguserprofile', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
            ('initiation_term', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['base.Term'])),
            ('bio', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'user_profiles', ['StudentOrgUserProfile'])


    def backwards(self, orm):
        # Deleting model 'UserProfile'
        db.delete_table(u'user_profiles_userprofile')

        # Deleting model 'CollegeStudentInfo'
        db.delete_table(u'user_profiles_collegestudentinfo')

        # Removing M2M table for field major on 'CollegeStudentInfo'
        db.delete_table(db.shorten_name(u'user_profiles_collegestudentinfo_major'))

        # Deleting model 'StudentOrgUserProfile'
        db.delete_table(u'user_profiles_studentorguserprofile')


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
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'base.major': {
            'Meta': {'ordering': "('long_name',)", 'unique_together': "(('university', 'short_name'),)", 'object_name': 'Major'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'long_name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'university': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['base.University']"}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        u'base.term': {
            'Meta': {'ordering': "('id',)", 'unique_together': "(('term', 'year'),)", 'object_name': 'Term'},
            'current': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'term': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'year': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        },
        u'base.university': {
            'Meta': {'ordering': "('long_name',)", 'object_name': 'University'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'long_name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'short_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '8'}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'user_profiles.collegestudentinfo': {
            'Meta': {'object_name': 'CollegeStudentInfo'},
            'grad_term': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'to': u"orm['base.Term']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'id_code': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'major': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['base.Major']", 'null': 'True', 'symmetrical': 'False'}),
            'start_term': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'to': u"orm['base.Term']"}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True'})
        },
        u'user_profiles.studentorguserprofile': {
            'Meta': {'ordering': "('user',)", 'object_name': 'StudentOrgUserProfile'},
            'bio': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'initiation_term': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['base.Term']"}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True'})
        },
        u'user_profiles.userprofile': {
            'Meta': {'ordering': "('preferred_name', 'user__last_name')", 'object_name': 'UserProfile'},
            'alt_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'birthday': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'cell_phone': ('localflavor.us.models.PhoneNumberField', [], {'max_length': '20', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'home_phone': ('localflavor.us.models.PhoneNumberField', [], {'max_length': '20', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'international_address': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'local_address1': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'local_address2': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'local_city': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'local_state': ('localflavor.us.models.USStateField', [], {'max_length': '2', 'blank': 'True'}),
            'local_zip': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'middle_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'perm_address1': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'perm_address2': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'perm_city': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'perm_state': ('localflavor.us.models.USStateField', [], {'default': "'CA'", 'max_length': '2', 'blank': 'True'}),
            'perm_zip': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'picture': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'preferred_name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '64', 'blank': 'True'}),
            'receive_text': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True'})
        }
    }

    complete_apps = ['user_profiles']