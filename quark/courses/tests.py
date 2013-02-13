from django.test import TestCase

from quark.courses.models import Course
from quark.courses.models import Department
from quark.courses.models import Instructor


def make_test_department():
    test_department = Department(
        long_name='Test Department 1',
        short_name='Tst Dep 1',
        abbreviation='TEST DEPT 1')
    test_department.save()
    return test_department


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
