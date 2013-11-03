from django.contrib.auth import get_user_model
from django.test import TestCase

from quark.base.models import Term
from quark.courses.models import Course
from quark.courses.models import CourseInstance
from quark.courses.models import Department
from quark.courses.models import Instructor
from quark.course_surveys.models import Survey
from quark.exams.models import Exam


def make_test_department():
    test_department = Department(
        long_name='Test Department 1',
        short_name='Tst Dep 1',
        abbreviation='TEST DEPT 1')
    test_department.save()
    return test_department


class CoursesTestCase(TestCase):
    fixtures = ['site']

    def setUp(self):
        self.dept_cs = Department(
            long_name='Computer Science',
            short_name='CS',
            abbreviation='COMPSCI')
        self.dept_cs.save()
        self.dept_ee = Department(
            long_name='Electrical Engineering',
            short_name='EE',
            abbreviation='EL ENG')
        self.dept_ee.save()
        self.course_cs_1 = Course(department=self.dept_cs, number='1')
        self.course_cs_1.save()
        self.course_ee_1 = Course(department=self.dept_ee, number='1')
        self.course_ee_1.save()
        self.instructor_cs = Instructor(first_name='Tau', last_name='Bate',
                                        department=self.dept_cs)
        self.instructor_cs.save()
        self.instructor_ee = Instructor(first_name='Pi', last_name='Bent',
                                        department=self.dept_ee)
        self.instructor_ee.save()
        self.term = Term(term='sp', year=2013, current=True)
        self.term.save()
        self.course_instance_cs_1 = CourseInstance(
            term=self.term,
            course=self.course_cs_1)
        self.course_instance_cs_1.save()
        self.course_instance_cs_1.instructors.add(self.instructor_cs)
        self.course_instance_cs_1.save()
        self.course_instance_ee_1 = CourseInstance(
            term=self.term,
            course=self.course_ee_1)
        self.course_instance_ee_1.save()
        self.course_instance_ee_1.instructors.add(self.instructor_ee)
        self.course_instance_ee_1.save()
        self.user = get_user_model().objects.create_user(
            username='tbpUser',
            email='tbp.berkeley.edu',
            password='testpassword',
            first_name='tbp',
            last_name='user')
        self.user.save()
        self.survey_cs_1 = Survey(
            course=self.course_cs_1,
            term=self.term,
            instructor=self.instructor_cs,
            prof_rating=5,
            course_rating=5,
            time_commitment=5,
            comments='Test comments',
            submitter=self.user,
            published=True)
        self.survey_cs_1.save()
        self.survey_cs_1_b = Survey(
            course=self.course_cs_1,
            term=self.term,
            instructor=self.instructor_cs,
            prof_rating=0,
            course_rating=5,
            time_commitment=0,
            comments='Test comments',
            submitter=self.user,
            published=True)
        self.survey_cs_1_b.save()
        self.exam_ee_1 = Exam(
            course_instance=self.course_instance_ee_1,
            submitter=self.user,
            exam_number=Exam.FINAL,
            exam_type=Exam.EXAM,
            unique_id='abcdefg',
            file_ext='.pdf',
            verified=True)
        self.exam_ee_1.save()


class DepartmentTest(TestCase):
    def test_save(self):
        test_department = Department(
            long_name='Test Department 2',
            short_name='Tst Dep 2',
            abbreviation='test dept 2')
        self.assertFalse(test_department.slug)
        test_department.save()
        self.assertEquals(test_department.abbreviation, 'TEST DEPT 2')
        self.assertEquals(test_department.slug, 'tst-dep-2')
        test_department.short_name = 'Tst Dep 2 New'
        self.assertEquals(test_department.slug, 'tst-dep-2')
        test_department.save()
        self.assertEquals(test_department.slug, 'tst-dep-2-new')
        test_department.full_clean()


class CourseTest(TestCase):
    def setUp(self):
        self.test_department = make_test_department()
        self.test_department_2 = Department(
            long_name='Test Department 2',
            short_name='Tst Dep 2',
            abbreviation='TEST DEPT 2')
        self.test_department_2.save()
        self.test_course_1 = Course(
            department=self.test_department,
            number='61a',
            title='TestDept1 61a')
        self.test_course_1.save()
        self.test_course_2 = Course(
            department=self.test_department,
            number='h61a',
            title='Honors TestDept1 61a')
        self.test_course_2.save()
        self.test_course_3 = Course(
            department=self.test_department,
            number='61b',
            title='TestDept1 61b')
        self.test_course_3.save()
        self.test_course_4 = Course(
            department=self.test_department,
            number='70',
            title='TestDept1 70')
        self.test_course_4.save()
        self.test_course_5 = Course(
            department=self.test_department_2,
            number='C30',
            title='TestDept2 C30')
        self.test_course_5.save()
        self.test_course_6 = Course(
            department=self.test_department_2,
            number='70',
            title='TestDept2 70')
        self.test_course_6.save()
        self.test_course_7 = Course(
            department=self.test_department_2,
            number='130AC',
            title='TestDept2 130AC')
        self.test_course_7.save()
        self.test_course_8 = Course(
            department=self.test_department_2,
            number='C130AC',
            title='TestDept2 C130AC')
        self.test_course_8.save()
        self.test_course_9 = Course(
            department=self.test_department_2,
            number='H130AC',
            title='TestDept2 Honors 130AC')
        self.test_course_9.save()

    def tearDown(self):
        self.test_department.full_clean()

    def test_save(self):
        self.assertEquals(self.test_course_2.number, 'H61A')

    def test_abbreviation(self):
        self.assertEquals(self.test_course_2.abbreviation(), 'Tst Dep 1 H61A')

    def test_get_display_name(self):
        self.assertEquals(self.test_course_2.get_display_name(),
                          'Test Department 1 H61A')

    def test_lessthan(self):
        self.assertFalse(self.test_course_1 < self.test_course_1)
        self.assertTrue(self.test_course_1 < self.test_course_2)
        self.assertTrue(self.test_course_1 < self.test_course_3)
        self.assertTrue(self.test_course_1 < self.test_course_4)
        self.assertTrue(self.test_course_1 < self.test_course_5)
        self.assertTrue(self.test_course_1 < self.test_course_6)
        self.assertTrue(self.test_course_2 < self.test_course_3)
        self.assertTrue(self.test_course_2 < self.test_course_4)
        self.assertTrue(self.test_course_4 < self.test_course_5)
        self.assertTrue(self.test_course_4 < self.test_course_6)
        self.assertTrue(self.test_course_4 < self.test_course_7)
        self.assertTrue(self.test_course_4 < self.test_course_8)
        self.assertTrue(self.test_course_7 < self.test_course_8)
        self.assertTrue(self.test_course_7 < self.test_course_9)
        self.assertTrue(self.test_course_8 < self.test_course_9)
        self.assertFalse(self.test_course_1 < self.test_department)

    def test_equals(self):
        self.assertTrue(self.test_course_1 == self.test_course_1)
        self.assertFalse(self.test_course_4 == self.test_course_6)
        self.assertFalse(self.test_course_7 == self.test_course_8)
        self.assertFalse(self.test_course_8 == self.test_course_9)
        self.assertFalse(self.test_course_1 == self.test_department)

    def test_other_comparison_methods(self):
        self.assertTrue(self.test_course_2 <= self.test_course_2)
        self.assertTrue(self.test_course_2 <= self.test_course_3)
        self.assertTrue(self.test_course_2 != self.test_course_3)
        self.assertTrue(self.test_course_4 > self.test_course_1)
        self.assertTrue(self.test_course_4 >= self.test_course_4)
        self.assertTrue(self.test_course_4 >= self.test_course_3)
        self.assertFalse(self.test_course_1 <= self.test_department)
        self.assertFalse(self.test_course_1 > self.test_department)
        self.assertFalse(self.test_course_1 >= self.test_department)
        self.assertTrue(self.test_course_1 != self.test_department)

    def test_sort(self):
        sorted_list = [self.test_course_1, self.test_course_2,
                       self.test_course_3, self.test_course_4,
                       self.test_course_5, self.test_course_6,
                       self.test_course_7, self.test_course_8,
                       self.test_course_9]
        test_list = [self.test_course_1, self.test_course_3,
                     self.test_course_5, self.test_course_7,
                     self.test_course_9, self.test_course_4,
                     self.test_course_6, self.test_course_8,
                     self.test_course_2]
        self.assertNotEqual(test_list, sorted_list)
        test_list.sort()
        # Correct ordering:
        # TD1 61A, TD1 H61A, TD1 61B, TD1 70, TD2 C30,
        # TD2 70, TD2 130AC, TD2 C130AC, TD2 H130AC
        self.assertEquals(test_list, sorted_list)


class InstructorTest(TestCase):
    def setUp(self):
        self.test_department = make_test_department()
        self.test_instructor = Instructor(
            first_name='Tau',
            last_name='Betapi',
            department=self.test_department)
        self.test_instructor.save()

    def tearDown(self):
        self.test_department.full_clean()

    def test_full_name(self):
        self.assertEquals(self.test_instructor.full_name(), 'Tau Betapi')


class DepartmentListViewTest(CoursesTestCase):
    def test_response(self):
        resp = self.client.get('/courses/')
        # A successful HTTP GET request has status code 200
        self.assertEqual(resp.status_code, 200)

    def test_dept_filter(self):
        resp = self.client.get('/courses/')
        self.assertEqual(resp.context['department_list'].count(), 2)
        self.exam_ee_1.verified = False
        self.exam_ee_1.save()
        self.survey_cs_1.published = False
        self.survey_cs_1.save()
        self.survey_cs_1_b.published = False
        self.survey_cs_1_b.save()
        resp = self.client.get('/courses/')
        # Filters out departments that don't have exams/surveys
        self.assertEqual(resp.context['department_list'].count(), 0)


class CourseListViewTest(CoursesTestCase):
    def test_response(self):
        resp = self.client.get('/courses/Cs/')
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get('/courses/bad-dept/')
        self.assertEqual(resp.status_code, 404)

    def test_course_filter(self):
        resp = self.client.get('/courses/cs/')
        self.assertEqual(resp.context['course_list'].count(), 1)
        resp = self.client.get('/courses/ee/')
        self.assertEqual(resp.context['course_list'].count(), 1)
        self.survey_cs_1.published = False
        self.survey_cs_1.save()
        self.survey_cs_1_b.published = False
        self.survey_cs_1_b.save()
        self.exam_ee_1.verified = False
        self.exam_ee_1.save()
        # Filters out courses that don't have exams/surveys
        resp = self.client.get('/courses/cs/')
        self.assertEqual(resp.status_code, 404)
        resp = self.client.get('/courses/ee/')
        self.assertEqual(resp.status_code, 404)


class CourseDetailViewTest(CoursesTestCase):
    def test_response(self):
        resp = self.client.get('/courses/cs/1/')
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get('/courses/bad-dept/1/')
        self.assertEqual(resp.status_code, 404)
        resp = self.client.get('/courses/cs/9999/')
        self.assertEqual(resp.status_code, 404)

    def test_course_details(self):
        resp = self.client.get('/courses/cs/1/')
        self.assertEqual(resp.context['course'].pk,
                         self.course_cs_1.pk)
        self.assertEqual(resp.context['course_instances'].count(), 1)
        self.assertEqual(resp.context['exams'].count(), 0)
        self.assertEqual(resp.context['surveys'].count(), 2)
        self.assertEqual(resp.context['instructors'].count(), 1)

    def test_course_aggregates(self):
        resp = self.client.get('/courses/cs/1/')
        self.assertEqual(resp.context['total_course_ratings_avg'], 5)
        # Value for this dictionary is (avg_prof_rating, avg_course_rating)
        self.assertEqual(
            resp.context['prof_ratings_avg'][
                self.instructor_cs.full_name()], 2.5)
        self.assertEqual(
            resp.context['course_ratings_avg'][
                self.instructor_cs.full_name()], 5)


class InstructorDetailViewTest(CoursesTestCase):
    def test_response(self):
        resp = self.client.get('/courses/instructors/99999999/')
        self.assertEqual(resp.status_code, 404)
        resp = self.client.get(
            '/courses/instructors/%d/' % (self.instructor_cs.pk))
        self.assertEqual(resp.status_code, 200)

    def test_instructor_details(self):
        resp = self.client.get(
            '/courses/instructors/%d/' % (self.instructor_cs.pk))
        self.assertEqual(resp.context['instructor'].pk, self.instructor_cs.pk)
        self.assertEqual(resp.context['course_instances'].count(), 1)
        self.assertEqual(resp.context['exams'].count(), 0)
        self.assertEqual(resp.context['surveys'].count(), 2)
        self.assertEqual(resp.context['total_prof_ratings_avg'], 2.5)
        # Value for this dictionary is (avg_prof_rating, avg_course_rating)
        self.assertEqual(
            resp.context['course_ratings_avg'][
                self.course_cs_1.abbreviation()], 5)
        self.assertEqual(
            resp.context['prof_ratings_avg'][
                self.course_cs_1.abbreviation()], 2.5)
