import os
import shutil

from django.conf import settings
from django.core.files import File
from django.test import TestCase
from django.test.utils import override_settings

from quark.base.models import Term
from quark.courses.models import CourseInstance
from quark.exams.models import Exam
from quark.exams.models import ExamFlag
from quark.exams.models import InstructorPermission


def make_test_exam(number):
    test_file = open('test.txt', 'w+')
    test_file.write('This is a test file.')
    test_exam = Exam(
        course_instance=CourseInstance.objects.get(pk=number),
        exam_number=Exam.MT1, exam_type=Exam.EXAM, verified=True,
        exam_file=File(test_file))
    test_exam.save()
    test_exam.course.department.save()
    test_exam.course.save()
    test_exam.course_instance.save()
    return test_exam


@override_settings(
    MEDIA_ROOT=os.path.join(settings.WORKSPACE_ROOT, 'media', 'tests'))
class ExamTest(TestCase):
    fixtures = ['test/course_instance.yaml']

    def setUp(self):
        self.test_exam1 = make_test_exam(10000)
        self.test_exam2 = make_test_exam(20000)
        self.test_exam3 = make_test_exam(30000)

        self.permission1 = InstructorPermission.objects.get(pk=100000)
        self.permission2 = InstructorPermission.objects.get(pk=200000)
        self.permission3 = InstructorPermission.objects.get(pk=300000)

    @classmethod
    def tearDownClass(cls):
        os.remove('test.txt')
        shutil.rmtree(os.path.join(settings.WORKSPACE_ROOT, 'media', 'tests'),
                      ignore_errors=True)

    def test_exam_manager(self):
        # All of the 3 test exams have approval (verified, no flags, not
        # blacklisted) when created in setUp:
        self.assertEquals(3, Exam.objects.get_approved().count())

        # Remove test_exam1 verification:
        self.test_exam1.verified = False
        self.test_exam1.save()
        approved_set = Exam.objects.get_approved()
        self.assertEquals(2, approved_set.count())
        self.assertNotIn(self.test_exam1, approved_set)

    def test_properites(self):
        self.assertEquals(self.test_exam1.file_ext, '.txt')
        self.assertNotEqual(self.test_exam1.unique_id, '')
        self.assertEquals(
            self.test_exam1.get_download_file_name(),
            '{course}-{term}-{number}-{instructors}-{type}{ext}'.format(
                course='test100', term=Term.SPRING + '2013',
                number=Exam.MT1, instructors='Beta_Tau',
                type=Exam.EXAM, ext='.txt'))
        self.assertEquals(
            unicode(self.test_exam1),
            ('{term} {number} {type} for {course}, taught by '
             '{instructors}').format(
                term='Spring 2013', number='Midterm 1', type='Exam',
                course='Test 100', instructors='Beta, Tau'))

    def test_flag_properites(self):
        exam_flag = ExamFlag(exam=self.test_exam1)
        self.assertEquals(
            unicode(exam_flag), unicode(self.test_exam1) + ' Flag')
        self.assertFalse(exam_flag.resolved)

    def test_delete_exam_with_file(self):
        file_name = self.test_exam1.get_absolute_pathname()
        self.assertTrue(os.path.exists(file_name))
        self.test_exam1.delete()
        self.assertFalse(os.path.exists(file_name))

    def test_delete_exam_without_file(self):
        # pylint: disable=E1103
        self.test_exam1.exam_file.delete()
        file_name = self.test_exam1.get_absolute_pathname()
        self.test_exam1.delete()
        self.assertFalse(os.path.exists(file_name))

    def test_response(self):
        resp = self.client.get('/courses/Test/100/')
        # A successful HTTP GET request has status code 200
        self.assertEqual(resp.status_code, 200)

    def test_multiple_blacklists_and_exams(self):
        """permission 1 affects only Exam 1.
        permission 2 affects Exam 1 and Exam 2.
        permission 3 affects Exam 2 and Exam 3.
        """
        # pylint: disable=R0915
        resp = self.client.get('/courses/Test/100/')
        # All exams with 0 blacklists
        self.assertEqual(resp.context['exams'].count(), 3)
        # Exam 1 with 1 blacklist, Exam 2 with 0, Exam 3 with 0
        self.permission1.permission_allowed = False
        self.permission1.save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        self.test_exam2 = Exam.objects.get(pk=self.test_exam2.pk)
        self.test_exam3 = Exam.objects.get(pk=self.test_exam3.pk)
        self.assertTrue(self.test_exam1.blacklisted)
        self.assertFalse(self.test_exam2.blacklisted)
        self.assertFalse(self.test_exam3.blacklisted)
        resp = self.client.get('/courses/Test/100/')
        self.assertEqual(resp.context['exams'].count(), 2)
        # Exam 1 with 2 blacklists, Exam 2 with 1, Exam 3 with 0
        self.permission2.permission_allowed = False
        self.permission2.save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        self.test_exam2 = Exam.objects.get(pk=self.test_exam2.pk)
        self.test_exam3 = Exam.objects.get(pk=self.test_exam3.pk)
        self.assertTrue(self.test_exam1.blacklisted)
        self.assertTrue(self.test_exam2.blacklisted)
        self.assertFalse(self.test_exam3.blacklisted)
        resp = self.client.get('/courses/Test/100/')
        self.assertEqual(resp.context['exams'].count(), 1)
        # Exam 1 with 1 blacklists, Exam 2 with 0, Exam 3 with 0
        self.permission2.permission_allowed = True
        self.permission2.save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        self.test_exam2 = Exam.objects.get(pk=self.test_exam2.pk)
        self.test_exam3 = Exam.objects.get(pk=self.test_exam3.pk)
        self.assertTrue(self.test_exam1.blacklisted)
        self.assertFalse(self.test_exam2.blacklisted)
        self.assertFalse(self.test_exam3.blacklisted)
        resp = self.client.get('/courses/Test/100/')
        self.assertEqual(resp.context['exams'].count(), 2)
        # Exam 1 with 1 blacklists, Exam 2 with 1, Exam 3 with 1
        self.permission3.permission_allowed = False
        self.permission3.save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        self.test_exam2 = Exam.objects.get(pk=self.test_exam2.pk)
        self.test_exam3 = Exam.objects.get(pk=self.test_exam3.pk)
        self.assertTrue(self.test_exam1.blacklisted)
        self.assertTrue(self.test_exam2.blacklisted)
        self.assertTrue(self.test_exam3.blacklisted)
        resp = self.client.get('/courses/Test/100/')
        self.assertEqual(resp.context['exams'].count(), 0)
        # Exam 1 with 2 blacklists, Exam 2 with 2, Exam 3 with 1
        self.permission2.permission_allowed = False
        self.permission2.save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        self.test_exam2 = Exam.objects.get(pk=self.test_exam2.pk)
        self.test_exam3 = Exam.objects.get(pk=self.test_exam3.pk)
        self.assertTrue(self.test_exam1.blacklisted)
        self.assertTrue(self.test_exam2.blacklisted)
        self.assertTrue(self.test_exam3.blacklisted)
        resp = self.client.get('/courses/Test/100/')
        self.assertEqual(resp.context['exams'].count(), 0)
        # Exam 1 with 2 blacklists, Exam 2 with 1, Exam 3 with 0
        self.permission3.permission_allowed = True
        self.permission3.save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        self.test_exam2 = Exam.objects.get(pk=self.test_exam2.pk)
        self.test_exam3 = Exam.objects.get(pk=self.test_exam3.pk)
        self.assertTrue(self.test_exam1.blacklisted)
        self.assertTrue(self.test_exam2.blacklisted)
        self.assertFalse(self.test_exam3.blacklisted)
        resp = self.client.get('/courses/Test/100/')
        self.assertEqual(resp.context['exams'].count(), 1)
        # Exam 1 with 1 blacklist, Exam 2 with 0, Exam 3 with 0
        self.permission2.permission_allowed = True
        self.permission2.save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        self.test_exam2 = Exam.objects.get(pk=self.test_exam2.pk)
        self.test_exam3 = Exam.objects.get(pk=self.test_exam3.pk)
        self.assertTrue(self.test_exam1.blacklisted)
        self.assertFalse(self.test_exam2.blacklisted)
        self.assertFalse(self.test_exam3.blacklisted)
        resp = self.client.get('/courses/Test/100/')
        self.assertEqual(resp.context['exams'].count(), 2)
        # Exam 1 with 0 blacklists, Exam 2 with 0, Exam 3 with 0
        self.permission1.permission_allowed = True
        self.permission1.save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        self.test_exam2 = Exam.objects.get(pk=self.test_exam2.pk)
        self.test_exam3 = Exam.objects.get(pk=self.test_exam3.pk)
        self.assertFalse(self.test_exam1.blacklisted)
        self.assertFalse(self.test_exam2.blacklisted)
        self.assertFalse(self.test_exam3.blacklisted)
        resp = self.client.get('/courses/Test/100/')
        self.assertEqual(resp.context['exams'].count(), 3)
        # Exam 1 with 0 blacklist, Exam 2 with 1, Exam 3 with 1
        self.permission3.permission_allowed = False
        self.permission3.save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        self.test_exam2 = Exam.objects.get(pk=self.test_exam2.pk)
        self.test_exam3 = Exam.objects.get(pk=self.test_exam3.pk)
        self.assertFalse(self.test_exam1.blacklisted)
        self.assertTrue(self.test_exam2.blacklisted)
        self.assertTrue(self.test_exam3.blacklisted)
        resp = self.client.get('/courses/Test/100/')
        self.assertEqual(resp.context['exams'].count(), 1)
        # Exam 1 with 1 blacklist, Exam 2 with 2, Exam 3 with 1
        self.permission2.permission_allowed = False
        self.permission2.save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        self.test_exam2 = Exam.objects.get(pk=self.test_exam2.pk)
        self.test_exam3 = Exam.objects.get(pk=self.test_exam3.pk)
        self.assertTrue(self.test_exam1.blacklisted)
        self.assertTrue(self.test_exam2.blacklisted)
        self.assertTrue(self.test_exam3.blacklisted)
        resp = self.client.get('/courses/Test/100/')
        self.assertEqual(resp.context['exams'].count(), 0)
        # Exam 1 with 0 blacklists, Exam 2 with 1, Exam 3 with 1
        self.permission2.permission_allowed = True
        self.permission2.save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        self.test_exam2 = Exam.objects.get(pk=self.test_exam2.pk)
        self.test_exam3 = Exam.objects.get(pk=self.test_exam3.pk)
        self.assertFalse(self.test_exam1.blacklisted)
        self.assertTrue(self.test_exam2.blacklisted)
        self.assertTrue(self.test_exam3.blacklisted)
        resp = self.client.get('/courses/Test/100/')
        self.assertEqual(resp.context['exams'].count(), 1)
        # Exam 1 with 0 blacklists, Exam 2 with 0, Exam 3 with 0
        self.permission3.permission_allowed = True
        self.permission3.save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        self.test_exam2 = Exam.objects.get(pk=self.test_exam2.pk)
        self.test_exam3 = Exam.objects.get(pk=self.test_exam3.pk)
        self.assertFalse(self.test_exam1.blacklisted)
        self.assertFalse(self.test_exam2.blacklisted)
        self.assertFalse(self.test_exam3.blacklisted)
        resp = self.client.get('/courses/Test/100/')
        self.assertEqual(resp.context['exams'].count(), 3)

    def test_flags_verified_and_blacklist(self):
        """Tests all 8 combinations of flags, blacklisted, and verified."""
        # pylint: disable=W0612
        self.assertTrue(self.test_exam1.flags <= ExamFlag.LIMIT)
        self.assertTrue(not self.test_exam1.blacklisted)
        self.assertTrue(self.test_exam1.verified)
        resp = self.client.get('/courses/Test/100/')
        self.assertEqual(resp.context['exams'].count(), 3)
        # Under flag limit, not blacklisted, verified
        exam_flag_list = []
        for i in range(0, ExamFlag.LIMIT):
            exam_flag = ExamFlag(exam=self.test_exam1)
            exam_flag.save()
            exam_flag_list.append(exam_flag)
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        self.assertTrue(self.test_exam1.flags <= ExamFlag.LIMIT)
        self.assertTrue(not self.test_exam1.blacklisted)
        self.assertTrue(self.test_exam1.verified)
        resp = self.client.get('/courses/Test/100/')
        self.assertEqual(resp.context['exams'].count(), 3)
        # Over flag limit, not blacklisted, verified
        last_exam_flag = ExamFlag(exam=self.test_exam1)
        last_exam_flag.save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        self.assertFalse(self.test_exam1.flags <= ExamFlag.LIMIT)
        self.assertTrue(not self.test_exam1.blacklisted)
        self.assertTrue(self.test_exam1.verified)
        resp = self.client.get('/courses/Test/100/')
        self.assertEqual(resp.context['exams'].count(), 2)
        # Under flag limit, blacklisted, verified
        exam_flag_list[0].resolved = True
        exam_flag_list[0].save()
        self.permission1.permission_allowed = False
        self.permission1.save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        self.assertTrue(self.test_exam1.flags <= ExamFlag.LIMIT)
        self.assertFalse(not self.test_exam1.blacklisted)
        self.assertTrue(self.test_exam1.verified)
        resp = self.client.get('/courses/Test/100/')
        self.assertEqual(resp.context['exams'].count(), 2)
        # Under flag limit, not blacklisted, not verified
        self.permission1.permission_allowed = True
        self.permission1.save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        self.test_exam1.verified = False
        self.test_exam1.save()
        self.assertTrue(self.test_exam1.flags <= ExamFlag.LIMIT)
        self.assertTrue(not self.test_exam1.blacklisted)
        self.assertFalse(self.test_exam1.verified)
        resp = self.client.get('/courses/Test/100/')
        self.assertEqual(resp.context['exams'].count(), 2)
        # Over flag limit, not blacklisted, not verified
        exam_flag_list[0].resolved = False
        exam_flag_list[0].save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        self.assertFalse(self.test_exam1.flags <= ExamFlag.LIMIT)
        self.assertTrue(not self.test_exam1.blacklisted)
        self.assertFalse(self.test_exam1.verified)
        resp = self.client.get('/courses/Test/100/')
        self.assertEqual(resp.context['exams'].count(), 2)
        # Over flag limit, blacklisted, verified
        self.test_exam1.verified = True
        self.test_exam1.save()
        self.permission1.permission_allowed = False
        self.permission1.save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        self.assertFalse(self.test_exam1.flags <= ExamFlag.LIMIT)
        self.assertFalse(not self.test_exam1.blacklisted)
        self.assertTrue(self.test_exam1.verified)
        resp = self.client.get('/courses/Test/100/')
        self.assertEqual(resp.context['exams'].count(), 2)
        # Under flag limit, blacklisted, not verified
        exam_flag_list[0].resolved = True
        exam_flag_list[0].save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        self.test_exam1.verified = False
        self.test_exam1.save()
        self.assertTrue(self.test_exam1.flags <= ExamFlag.LIMIT)
        self.assertFalse(not self.test_exam1.blacklisted)
        self.assertFalse(self.test_exam1.verified)
        resp = self.client.get('/courses/Test/100/')
        self.assertEqual(resp.context['exams'].count(), 2)
        # Over flag limit, blacklisted, not verified
        exam_flag_list[0].resolved = False
        exam_flag_list[0].save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        self.assertFalse(self.test_exam1.flags <= ExamFlag.LIMIT)
        self.assertFalse(not self.test_exam1.blacklisted)
        self.assertFalse(self.test_exam1.verified)
        resp = self.client.get('/courses/Test/100/')
        self.assertEqual(resp.context['exams'].count(), 2)
