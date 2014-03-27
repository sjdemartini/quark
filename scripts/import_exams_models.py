import re
import os
import uuid

from dateutil import parser
from django.contrib.auth import get_user_model
from django.core.files import File
from django.db.models import Count
from django.utils.timezone import get_current_timezone
from django.utils.timezone import make_aware

from quark.base.models import Term
from quark.courses.models import Course
from quark.courses.models import CourseInstance
from quark.courses.models import Department
from quark.courses.models import Instructor
from quark.exams.models import Exam
from quark.exams.models import ExamFlag
from quark.shortcuts import get_object_or_none
from scripts import get_json_data


NOIRO_EXAMS_LOCATION = '/var/testfiles/'
# Dictionary mapping the pk's of noiro Departments to the pk's of quark
# Departments and department abbreviations. This is necessary because the
# examfiles app in noiro used their own Department model instead of the
# Department model in the courses app. The abbreviations are used for getting
# the file that the exam corresponds to.
DEPARTMENT_CONVERSION = {
    1: (115, 'ne'),
    2: (27, 'chem'),
    3: (122, 'physics'),
    4: (99, 'mcb'),
    5: (90, 'mse'),
    6: (26, 'cheme'),
    7: (51, 'ee'),
    8: (77, 'ib'),
    9: (30, 'cee'),
    10: (91, 'math'),
    11: (92, 'me'),
    12: (155, 'stats'),
    13: (54, 'eng'),
    14: (75, 'ieor'),
    15: (52, 'cs'),
    16: (16, 'bioe'),
    17: (158, 'bio')}
EXAM_TYPE_CONVERSION = {'e': 'exam', 's': 'soln'}

user_model = get_user_model()
timezone = get_current_timezone()


def import_exams():
    # pylint: disable=R0912,R0914
    models = get_json_data('examfiles.exam.json')
    for model in models:
        fields = model['fields']

        year = int(fields['year'])
        semester = fields['semester']
        # Check for exams with unknown semesters
        if semester == '??':
            semester = Term.UNKNOWN
        # Check for exams with unknown years (all stored with years less than 5)
        if year < 5:
            term = None
        else:
            term, _ = Term.objects.get_or_create(term=semester, year=year)

        dept_pk, dept_abbreviation = DEPARTMENT_CONVERSION[fields['department']]
        department = Department.objects.get(pk=dept_pk)
        course, _ = Course.objects.get_or_create(
            department=department, number=fields['courseNumber'])

        # Some last names contain in parenthesis the section number or some
        # other information about the course, so remove that
        last_names = fields['professor']
        paren_index = last_names.find('(')
        if paren_index != -1:
            last_names = last_names[:paren_index]
        # Multiple last names may be separated by commas or underscores
        last_names = re.split(',|_', last_names.replace(' ', ''))
        instructors = []
        # Don't add any instructors to an exam if the instructor last name
        # contains "unknown"
        if 'unknown' not in last_names[0].lower():
            for last_name in last_names:
                instructor = Instructor.objects.filter(
                    last_name=last_name, department=department)
                if instructor.exists():
                    instructor = instructor[0]
                else:
                    instructor = Instructor.objects.create(
                        last_name=last_name, department=department)
                instructors.append(instructor)

        # Check if a course instance exists with the exact instructors given
        # and create a course instance if one doesn't exist
        course_instance = CourseInstance.objects.annotate(
            count=Count('instructors')).filter(
            count=len(instructors), course=course, term=term)
        for instructor in instructors:
            course_instance = course_instance.filter(instructors=instructor)
        if course_instance.exists():
            course_instance = course_instance[0]
        else:
            course_instance = CourseInstance.objects.create(
                term=term, course=course)
            course_instance.instructors.add(*instructors)
            course_instance.save()

        # Check for unknown exam numbers
        exam_number = fields['examNumber'].lower()
        if exam_number == 'unknown' or exam_number == 'mt':
            exam_number = Exam.UNKNOWN

        # Check manually whether an exam already exists rather than use
        # get_or_create because in order to specify a primary key for an exam
        # when it's created, a unique id needs to assigned at the same time as
        # well
        exam = Exam.objects.filter(
            course_instance=course_instance,
            exam_number=exam_number,
            exam_type=EXAM_TYPE_CONVERSION[fields['examOrSolution']])
        # Don't import exams that were already imported, or exams for the same
        # course instance but different file types
        if exam.exists():
            continue
        exam = Exam.objects.create(
            pk=model['pk'],
            course_instance=course_instance,
            exam_number=exam_number,
            exam_type=EXAM_TYPE_CONVERSION[fields['examOrSolution']],
            verified=fields['approved'],
            unique_id=uuid.uuid4().hex)

        if fields['submitter']:
            exam.submitter = user_model.objects.get(pk=fields['submitter'])
        # Exams use "unknown" as the semester in filenames if the semester
        # is unknown
        if semester == Term.UNKNOWN:
            semester = 'unknown'

        # Construct the old noiro filename for the exam file
        filename = ('{dept}{course_num}-{term}{year}-{number}-'
                    '{instructors}-{type}.{ext}').format(
            dept=dept_abbreviation,
            course_num=fields['courseNumber'],
            term=semester,
            year=fields['year'][2:],
            number=fields['examNumber'],
            instructors=fields['professor'],
            type=exam.exam_type,
            ext=fields['filetype'])

        exam_location = os.path.join(
            NOIRO_EXAMS_LOCATION, dept_abbreviation, filename)
        with open(exam_location, 'r') as exam_file:
            exam.exam_file = File(exam_file)
            exam.save()


def import_exam_flags():
    models = get_json_data('examfiles.examflag.json')
    for model in models:
        fields = model['fields']

        # Don't import flags for exams that weren't imported because they were
        # duplicates with a different file type
        exam = get_object_or_none(Exam, pk=fields['exam'])
        if not exam:
            continue

        exam_flag, _ = ExamFlag.objects.get_or_create(
            pk=model['pk'],
            exam=exam,
            reason=fields['reason'])

        # Convert the naive datetime into an aware datetime
        created = parser.parse(fields['created'])
        exam_flag.created = make_aware(created, timezone)
        exam_flag.save()
