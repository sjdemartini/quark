# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Department'
        db.create_table(u'courses_department', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('long_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('short_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=25)),
            ('abbreviation', self.gf('django.db.models.fields.CharField')(max_length=25)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=25)),
        ))
        db.send_create_signal(u'courses', ['Department'])

        # Adding model 'Course'
        db.create_table(u'courses_course', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('department', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['courses.Department'])),
            ('number', self.gf('django.db.models.fields.CharField')(max_length=10, db_index=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'courses', ['Course'])

        # Adding unique constraint on 'Course', fields ['department', 'number']
        db.create_unique(u'courses_course', ['department_id', 'number'])

        # Adding model 'Instructor'
        db.create_table(u'courses_instructor', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('middle_initial', self.gf('django.db.models.fields.CharField')(max_length=1, blank=True)),
            ('department', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['courses.Department'])),
            ('website', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
        ))
        db.send_create_signal(u'courses', ['Instructor'])

        # Adding unique constraint on 'Instructor', fields ['first_name', 'middle_initial', 'last_name', 'department']
        db.create_unique(u'courses_instructor', ['first_name', 'middle_initial', 'last_name', 'department_id'])

        # Adding model 'CourseInstance'
        db.create_table(u'courses_courseinstance', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('term', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.Term'], null=True)),
            ('course', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['courses.Course'])),
        ))
        db.send_create_signal(u'courses', ['CourseInstance'])

        # Adding M2M table for field instructors on 'CourseInstance'
        m2m_table_name = db.shorten_name(u'courses_courseinstance_instructors')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('courseinstance', models.ForeignKey(orm[u'courses.courseinstance'], null=False)),
            ('instructor', models.ForeignKey(orm[u'courses.instructor'], null=False))
        ))
        db.create_unique(m2m_table_name, ['courseinstance_id', 'instructor_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Instructor', fields ['first_name', 'middle_initial', 'last_name', 'department']
        db.delete_unique(u'courses_instructor', ['first_name', 'middle_initial', 'last_name', 'department_id'])

        # Removing unique constraint on 'Course', fields ['department', 'number']
        db.delete_unique(u'courses_course', ['department_id', 'number'])

        # Deleting model 'Department'
        db.delete_table(u'courses_department')

        # Deleting model 'Course'
        db.delete_table(u'courses_course')

        # Deleting model 'Instructor'
        db.delete_table(u'courses_instructor')

        # Deleting model 'CourseInstance'
        db.delete_table(u'courses_courseinstance')

        # Removing M2M table for field instructors on 'CourseInstance'
        db.delete_table(db.shorten_name(u'courses_courseinstance_instructors'))


    models = {
        u'base.term': {
            'Meta': {'ordering': "('id',)", 'unique_together': "(('term', 'year'),)", 'object_name': 'Term'},
            'current': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'term': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'year': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        },
        u'courses.course': {
            'Meta': {'unique_together': "(('department', 'number'),)", 'object_name': 'Course'},
            'department': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['courses.Department']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        },
        u'courses.courseinstance': {
            'Meta': {'object_name': 'CourseInstance'},
            'course': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['courses.Course']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instructors': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['courses.Instructor']", 'symmetrical': 'False'}),
            'term': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['base.Term']", 'null': 'True'})
        },
        u'courses.department': {
            'Meta': {'ordering': "('long_name',)", 'object_name': 'Department'},
            'abbreviation': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'long_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '25'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '25'})
        },
        u'courses.instructor': {
            'Meta': {'ordering': "('last_name', 'first_name', 'middle_initial')", 'unique_together': "(('first_name', 'middle_initial', 'last_name', 'department'),)", 'object_name': 'Instructor'},
            'department': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['courses.Department']"}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'middle_initial': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        }
    }

    complete_apps = ['courses']