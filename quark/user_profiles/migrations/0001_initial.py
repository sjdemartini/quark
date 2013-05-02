# -*- coding: utf-8 -*-
import datetime
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
            ('picture', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='profile_picture', null=True, to=orm['filer.Image'])),
            ('alt_email', self.gf('django.db.models.fields.EmailField')(max_length=75, blank=True)),
            ('cell_phone', self.gf('django_localflavor_us.models.PhoneNumberField')(max_length=20, blank=True)),
            ('home_phone', self.gf('django_localflavor_us.models.PhoneNumberField')(max_length=20, blank=True)),
            ('receive_text', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('local_address1', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('local_address2', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('local_city', self.gf('django.db.models.fields.CharField')(max_length=128, blank=True)),
            ('local_state', self.gf('django_localflavor_us.models.USStateField')(max_length=2, blank=True)),
            ('local_zip', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True)),
            ('perm_address1', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('perm_address2', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('perm_city', self.gf('django.db.models.fields.CharField')(max_length=128, blank=True)),
            ('perm_state', self.gf('django_localflavor_us.models.USStateField')(default='CA', max_length=2, blank=True)),
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
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], unique=True)),
            ('major', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.Major'], null=True)),
            ('start_term', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', null=True, to=orm['base.Term'])),
            ('grad_term', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', null=True, to=orm['base.Term'])),
        ))
        db.send_create_signal(u'user_profiles', ['CollegeStudentInfo'])

        # Adding model 'StudentOrgUserProfile'
        db.create_table(u'user_profiles_studentorguserprofile', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], unique=True)),
            ('initiation_term', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['base.Term'])),
            ('bio', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'user_profiles', ['StudentOrgUserProfile'])


    def backwards(self, orm):
        # Deleting model 'UserProfile'
        db.delete_table(u'user_profiles_userprofile')

        # Deleting model 'CollegeStudentInfo'
        db.delete_table(u'user_profiles_collegestudentinfo')

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
        'filer.file': {
            'Meta': {'object_name': 'File'},
            '_file_size': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'folder': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'all_files'", 'null': 'True', 'to': "orm['filer.Folder']"}),
            'has_all_mandatory_data': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'original_filename': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'owned_files'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'polymorphic_ctype': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'polymorphic_filer.file_set'", 'null': 'True', 'to': u"orm['contenttypes.ContentType']"}),
            'sha1': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '40', 'blank': 'True'}),
            'uploaded_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'filer.folder': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('parent', 'name'),)", 'object_name': 'Folder'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'filer_owned_folders'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['filer.Folder']"}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'uploaded_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'filer.image': {
            'Meta': {'object_name': 'Image', '_ormbases': ['filer.File']},
            '_height': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            '_width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'author': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'date_taken': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'default_alt_text': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'default_caption': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            u'file_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['filer.File']", 'unique': 'True', 'primary_key': 'True'}),
            'must_always_publish_author_credit': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'must_always_publish_copyright': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'subject_location': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '64', 'null': 'True', 'blank': 'True'})
        },
        u'user_profiles.collegestudentinfo': {
            'Meta': {'object_name': 'CollegeStudentInfo'},
            'grad_term': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'to': u"orm['base.Term']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'id_code': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'major': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['base.Major']", 'null': 'True'}),
            'start_term': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'to': u"orm['base.Term']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'unique': 'True'})
        },
        u'user_profiles.studentorguserprofile': {
            'Meta': {'ordering': "('user',)", 'object_name': 'StudentOrgUserProfile'},
            'bio': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'initiation_term': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['base.Term']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'unique': 'True'})
        },
        u'user_profiles.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'alt_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'birthday': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'cell_phone': ('django_localflavor_us.models.PhoneNumberField', [], {'max_length': '20', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'home_phone': ('django_localflavor_us.models.PhoneNumberField', [], {'max_length': '20', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'international_address': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'local_address1': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'local_address2': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'local_city': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'local_state': ('django_localflavor_us.models.USStateField', [], {'max_length': '2', 'blank': 'True'}),
            'local_zip': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'middle_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'perm_address1': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'perm_address2': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'perm_city': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'perm_state': ('django_localflavor_us.models.USStateField', [], {'default': "'CA'", 'max_length': '2', 'blank': 'True'}),
            'perm_zip': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'picture': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'profile_picture'", 'null': 'True', 'to': "orm['filer.Image']"}),
            'preferred_name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '64', 'blank': 'True'}),
            'receive_text': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True'})
        }
    }

    complete_apps = ['user_profiles']