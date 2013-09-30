import json
import os

from django.conf import settings

from quark.base.models import Term
from quark.courses.models import Course
from quark.courses.models import CourseInstance
from quark.courses.models import Department
from quark.courses.models import Instructor

from scripts.import_base_models import SEMESTER_TO_TERM


def import_departments():
    data_path = os.path.join(
        settings.WORKSPACE_ROOT, 'scripts', 'data', 'courses.department.json')
    departments = json.load(open(data_path, 'r'))
    for dept in departments:
        fields = dept['fields']
        Department.objects.get_or_create(
            pk=dept['pk'],
            long_name=fields['name'],
            short_name=fields['abbreviation'][0:25],
            abbreviation=fields['code'][0:25])


def import_courses():
    data_path = os.path.join(
        settings.WORKSPACE_ROOT, 'scripts', 'data', 'courses.course.json')
    courses = json.load(open(data_path, 'r'))
    for course in courses:
        fields = course['fields']
        Course.objects.get_or_create(
            pk=course['pk'],
            department=Department.objects.get(pk=fields['department']),
            number=fields['number'],
            description=fields['description'])


def import_instructors():
    data_path = os.path.join(
        settings.WORKSPACE_ROOT, 'scripts', 'data', 'courses.instructor.json')
    instructors = json.load(open(data_path, 'r'))
    for instructor in instructors:
        fields = instructor['fields']
        Instructor.objects.get_or_create(
            pk=instructor['pk'],
            first_name=fields['firstname'],
            last_name=fields['lastname'],
            department=Department.objects.get(pk=fields['department']),
            website=fields['website'])


def import_course_instances():
    data_path = os.path.join(
        settings.WORKSPACE_ROOT, 'scripts', 'data', 'courses.section.json')
    course_instances = json.load(open(data_path, 'r'))
    for course_instance in course_instances:
        fields = course_instance['fields']
        instance = CourseInstance.objects.get_or_create(
            pk=course_instance['pk'],
            term=Term.objects.get(pk=SEMESTER_TO_TERM[fields['semester']]),
            course=Course.objects.get(pk=fields['course']))[0]
        instance.instructors = Instructor.objects.filter(
            pk__in=fields['instructors'])
        instance.save()
