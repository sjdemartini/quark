from django.contrib.auth import get_user_model
from django.test import TestCase

from quark.base.models import Term
from quark.courses.models import Course
from quark.courses.models import Department
from quark.courses.models import Instructor
from quark.course_surveys.forms import courses_as_optgroups
from quark.course_surveys.forms import SurveyForm


class SurveyFormTest(TestCase):
    def setUp(self):
        self.department_cs = Department(
            long_name='Computer Science',
            short_name='CS',
            abbreviation='COMP SCI')
        self.department_cs.save()
        self.department_me = Department(
            long_name='Mechanical Engineering',
            short_name='ME',
            abbreviation='MEC ENG')
        self.department_me.save()
        self.course_cs1 = Course(
            department=self.department_cs,
            number='1')
        self.course_cs1.save()
        self.course_me50 = Course(
            department=self.department_me,
            number='50')
        self.course_me50.save()
        self.instructor_test = Instructor(
            first_name='Tau',
            last_name='Bate',
            department=self.department_cs)
        self.instructor_test.save()
        self.term_test = Term(
            term=Term.SPRING,
            year=2013,
            current=True)
        self.term_test.save()
        self.user_test = get_user_model().objects.create_user(
            username='taubate',
            email='tbp.berkeley.edu',
            password='testpassword',
            first_name='Tau',
            last_name='Bate')
        self.user_test.save()

    def test_courses_as_optgroups(self):
        optgroups = courses_as_optgroups()
        # optgrous[i] returns [dept.long_name, list of courses in dept]
        # optgroups[i][1] returns a list of tuples in the form of
        # (Course, Course.abbreviation())
        self.assertEqual(optgroups[0][0], self.department_cs.long_name)
        self.assertEqual(optgroups[1][1][0][0], self.course_me50)

    def test_valid_form(self):
        test_form = SurveyForm()
        self.assertFalse(test_form.is_valid())
        form_data = {
            'course': self.course_me50.pk,
            'term': self.term_test.pk,
            'instructor': self.instructor_test.pk,
            'prof_rating': 1,
            'course_rating': 2,
            'time_commitment': 3,
            'comments': 'Test Comment',
            'submitter': self.user_test.pk
        }
        test_form = SurveyForm(form_data)
        self.assertTrue(test_form.is_valid())
