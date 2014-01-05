from quark.base.models import Term
from quark.courses.models import Course
from quark.courses.models import CourseInstance
from quark.courses.models import Department
from quark.courses.models import Instructor
from scripts import get_json_data
from scripts.import_base_models import SEMESTER_TO_TERM


def import_departments():
    models = get_json_data('courses.department.json')
    for model in models:
        fields = model['fields']
        Department.objects.get_or_create(
            pk=model['pk'],
            long_name=fields['name'],
            short_name=fields['abbreviation'][0:25],
            abbreviation=fields['code'][0:25])


def import_courses():
    models = get_json_data('courses.course.json')
    for model in models:
        fields = model['fields']
        Course.objects.get_or_create(
            pk=model['pk'],
            department=Department.objects.get(pk=fields['department']),
            number=fields['number'],
            title=fields['title'],
            description=fields['description'])


def import_instructors():
    models = get_json_data('courses.instructor.json')
    for model in models:
        fields = model['fields']
        Instructor.objects.get_or_create(
            pk=model['pk'],
            first_name=fields['firstname'],
            last_name=fields['lastname'],
            department=Department.objects.get(pk=fields['department']),
            website=fields['website'])


def import_course_instances():
    models = get_json_data('courses.section.json')
    for model in models:
        fields = model['fields']
        instance = CourseInstance.objects.get_or_create(
            pk=model['pk'],
            term=Term.objects.get(pk=SEMESTER_TO_TERM[fields['semester']]),
            course=Course.objects.get(pk=fields['course']))[0]
        instance.instructors = Instructor.objects.filter(
            pk__in=fields['instructors'])
        instance.save()
