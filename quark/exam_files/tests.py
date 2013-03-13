import os
import shutil

from django.conf import settings
from django.core.files import File
from django.test import TestCase

from quark.base.models import Term
from quark.courses.models import CourseInstance
from quark.exam_files.models import Exam
from quark.exam_files.models import ExamFlag


def make_test_exam(number):
    test_file = open('test.txt', 'w+')
    test_file.write('This is a test file.')
    test_exam = Exam(
        course_instance=CourseInstance.objects.get(pk=number), exam=Exam.MT1,
        exam_type=Exam.EXAM, approved=True, exam_file=File(test_file))
    test_exam.save()
    test_exam.course_instance.course.department.save()
    return test_exam


class ExamTest(TestCase):
    fixtures = ['test/course_instance.yaml']

    def setUp(self):
        self.test_exam = make_test_exam(10000)
        self.folder = self.test_exam.unique_id[0:2]

    def tearDown(self):
        folder = os.path.join(
            settings.MEDIA_ROOT, Exam.EXAM_FILES_LOCATION, self.folder)
        shutil.rmtree(folder, ignore_errors=True)
        os.remove('test.txt')

    def test_properites(self):
        self.assertEquals(self.test_exam.file_ext, '.txt')
        self.assertNotEqual(self.test_exam.unique_id, '')
        self.assertEquals(self.test_exam.get_term_name(), 'Spring 2013')
        self.assertEquals(
            unicode(self.test_exam),
            '{course}-{term}-{exam}-{instructors}-{exam_type}{ext}'.format(
                course='tst-dep-1100', term=Term.SPRING + '2013',
                exam=Exam.MT1, instructors='Beta_Tau',
                exam_type=Exam.EXAM, ext='.txt'))


class ExamFlagTest(TestCase):
    fixtures = ['test/course_instance.yaml']

    def setUp(self):
        self.test_exam = make_test_exam(10000)
        self.folder = self.test_exam.unique_id[0:2]

    def tearDown(self):
        folder = os.path.join(
            settings.MEDIA_ROOT, Exam.EXAM_FILES_LOCATION, self.folder)
        shutil.rmtree(folder, ignore_errors=True)
        os.remove('test.txt')

    def test_properites(self):
        exam_flag = ExamFlag(exam=self.test_exam)
        self.assertEquals(
            unicode(exam_flag), unicode(self.test_exam) + ' Flag')
        self.assertFalse(exam_flag.resolved)


class InstructorPermissionTest(TestCase):
    fixtures = ['test/course_instance.yaml']

    def setUp(self):
        self.test_exam = make_test_exam(10000)
        self.folder = self.test_exam.unique_id[0:2]

    def tearDown(self):
        folder = os.path.join(
            settings.MEDIA_ROOT, Exam.EXAM_FILES_LOCATION, self.folder)
        shutil.rmtree(folder, ignore_errors=True)
        os.remove('test.txt')

    def test_properites(self):
        permission = list(self.test_exam.get_permissions())[0]
        self.assertIsNone(permission.permission_allowed)


class DeleteFileTest(TestCase):
    fixtures = ['test/course_instance.yaml']

    def setUp(self):
        self.test_exam = make_test_exam(10000)
        self.folder = self.test_exam.unique_id[0:2]

    def tearDown(self):
        folder = os.path.join(
            settings.MEDIA_ROOT, Exam.EXAM_FILES_LOCATION, self.folder)
        shutil.rmtree(folder, ignore_errors=True)
        os.remove('test.txt')

    def test_delete_exam_with_file(self):
        file_name = self.test_exam.get_absolute_pathname()
        self.assertTrue(os.path.exists(file_name))
        self.test_exam.delete()
        self.assertFalse(os.path.exists(file_name))

    def test_delete_exam_without_file(self):
        self.test_exam.exam_file.delete()
        file_name = self.test_exam.get_absolute_pathname()
        self.test_exam.delete()
        self.assertFalse(os.path.exists(file_name))


class HideExamTest(TestCase):
    fixtures = ['test/course_instance.yaml']

    def setUp(self):
        self.test_exam1 = make_test_exam(10000)
        self.test_exam2 = make_test_exam(20000)
        self.test_exam3 = make_test_exam(30000)
        self.folder1 = self.test_exam1.unique_id[0:2]
        self.folder2 = self.test_exam2.unique_id[0:2]
        self.folder3 = self.test_exam3.unique_id[0:2]

    def tearDown(self):
        folder1 = os.path.join(
            settings.MEDIA_ROOT, Exam.EXAM_FILES_LOCATION, self.folder1)
        folder2 = os.path.join(
            settings.MEDIA_ROOT, Exam.EXAM_FILES_LOCATION, self.folder2)
        folder3 = os.path.join(
            settings.MEDIA_ROOT, Exam.EXAM_FILES_LOCATION, self.folder3)
        shutil.rmtree(folder1, ignore_errors=True)
        shutil.rmtree(folder2, ignore_errors=True)
        shutil.rmtree(folder3, ignore_errors=True)
        os.remove('test.txt')

    def test_multiple_blacklists_and_exams(self):
        """Permission 1 affects only Exam 1.
        Permission 2 affects Exam 1 and Exam 2.
        Permission 3 affects Exam 2 and Exam 3.
        """
        # pylint: disable=W0612
        permission1 = list(self.test_exam1.get_permissions())[0]
        permission2 = list(self.test_exam2.get_permissions())[0]
        permission3 = list(self.test_exam3.get_permissions())[0]
        permission1.permission_allowed = False
        permission1.save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        self.test_exam2 = Exam.objects.get(pk=self.test_exam2.pk)
        self.test_exam3 = Exam.objects.get(pk=self.test_exam3.pk)
        # Exam 1 with 1 blacklist, Exam 2 with 0, Exam 3 with 0
        self.assertFalse(self.test_exam1.approved)
        self.assertTrue(self.test_exam2.approved)
        self.assertTrue(self.test_exam3.approved)
        permission2.permission_allowed = False
        permission2.save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        self.test_exam2 = Exam.objects.get(pk=self.test_exam2.pk)
        self.test_exam3 = Exam.objects.get(pk=self.test_exam3.pk)
        # Exam 1 with 2 blacklists, Exam 2 with 1, Exam 3 with 0
        self.assertFalse(self.test_exam1.approved)
        self.assertFalse(self.test_exam2.approved)
        self.assertTrue(self.test_exam3.approved)
        permission2.permission_allowed = True
        permission2.save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        self.test_exam2 = Exam.objects.get(pk=self.test_exam2.pk)
        self.test_exam3 = Exam.objects.get(pk=self.test_exam3.pk)
        # Exam 1 with 1 blacklists, Exam 2 with 0, Exam 3 with 0
        self.assertFalse(self.test_exam1.approved)
        self.assertTrue(self.test_exam2.approved)
        self.assertTrue(self.test_exam3.approved)
        permission3.permission_allowed = False
        permission3.save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        self.test_exam2 = Exam.objects.get(pk=self.test_exam2.pk)
        self.test_exam3 = Exam.objects.get(pk=self.test_exam3.pk)
        # Exam 1 with 1 blacklists, Exam 2 with 1, Exam 3 with 1
        self.assertFalse(self.test_exam1.approved)
        self.assertFalse(self.test_exam2.approved)
        self.assertFalse(self.test_exam3.approved)
        permission2.permission_allowed = False
        permission2.save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        self.test_exam2 = Exam.objects.get(pk=self.test_exam2.pk)
        self.test_exam3 = Exam.objects.get(pk=self.test_exam3.pk)
        # Exam 1 with 2 blacklists, Exam 2 with 2, Exam 3 with 1
        self.assertFalse(self.test_exam1.approved)
        self.assertFalse(self.test_exam2.approved)
        self.assertFalse(self.test_exam3.approved)
        permission3.permission_allowed = True
        permission3.save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        self.test_exam2 = Exam.objects.get(pk=self.test_exam2.pk)
        self.test_exam3 = Exam.objects.get(pk=self.test_exam3.pk)
        # Exam 1 with 2 blacklists, Exam 2 with 1, Exam 3 with 0
        self.assertFalse(self.test_exam1.approved)
        self.assertFalse(self.test_exam2.approved)
        self.assertTrue(self.test_exam3.approved)
        permission2.permission_allowed = True
        permission2.save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        self.test_exam2 = Exam.objects.get(pk=self.test_exam2.pk)
        self.test_exam3 = Exam.objects.get(pk=self.test_exam3.pk)
        # Exam 1 with 1 blacklist, Exam 2 with 0, Exam 3 with 0
        self.assertFalse(self.test_exam1.approved)
        self.assertTrue(self.test_exam2.approved)
        self.assertTrue(self.test_exam3.approved)
        permission1.permission_allowed = True
        permission1.save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        self.test_exam2 = Exam.objects.get(pk=self.test_exam2.pk)
        self.test_exam3 = Exam.objects.get(pk=self.test_exam3.pk)
        # Exam 1 with 0 blacklists, Exam 2 with 0, Exam 3 with 0
        self.assertTrue(self.test_exam1.approved)
        self.assertTrue(self.test_exam2.approved)
        self.assertTrue(self.test_exam3.approved)
        permission3.permission_allowed = False
        permission3.save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        self.test_exam2 = Exam.objects.get(pk=self.test_exam2.pk)
        self.test_exam3 = Exam.objects.get(pk=self.test_exam3.pk)
        # Exam 1 with 0 blacklist, Exam 2 with 1, Exam 3 with 1
        self.assertTrue(self.test_exam1.approved)
        self.assertFalse(self.test_exam2.approved)
        self.assertFalse(self.test_exam3.approved)
        permission2.permission_allowed = False
        permission2.save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        self.test_exam2 = Exam.objects.get(pk=self.test_exam2.pk)
        self.test_exam3 = Exam.objects.get(pk=self.test_exam3.pk)
        # Exam 1 with 1 blacklist, Exam 2 with 2, Exam 3 with 1
        self.assertFalse(self.test_exam1.approved)
        self.assertFalse(self.test_exam2.approved)
        self.assertFalse(self.test_exam3.approved)
        permission2.permission_allowed = True
        permission2.save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        self.test_exam2 = Exam.objects.get(pk=self.test_exam2.pk)
        self.test_exam3 = Exam.objects.get(pk=self.test_exam3.pk)
        # Exam 1 with 0 blacklists, Exam 2 with 1, Exam 3 with 1
        self.assertTrue(self.test_exam1.approved)
        self.assertFalse(self.test_exam2.approved)
        self.assertFalse(self.test_exam3.approved)
        permission3.permission_allowed = True
        permission3.save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        self.test_exam2 = Exam.objects.get(pk=self.test_exam2.pk)
        self.test_exam3 = Exam.objects.get(pk=self.test_exam3.pk)
        # Exam 1 with 0 blacklists, Exam 2 with 0, Exam 3 with 0
        self.assertTrue(self.test_exam1.approved)
        self.assertTrue(self.test_exam2.approved)
        self.assertTrue(self.test_exam3.approved)

    def test_exam_limit_and_blacklist(self):
        # pylint: disable=W0612
        self.assertTrue(self.test_exam1.approved)
        exam_flag_list = []
        for i in range(0, ExamFlag.LIMIT):
            exam_flag = ExamFlag(exam=self.test_exam1)
            exam_flag.save()
            exam_flag_list.append(exam_flag)
        # Under flag limit, not blacklisted
        self.assertTrue(self.test_exam1.approved)
        last_exam_flag = ExamFlag(exam=self.test_exam1)
        last_exam_flag.save()
        # Over flag limit, not blacklisted
        self.assertFalse(self.test_exam1.approved)
        permission1 = list(self.test_exam1.get_permissions())[0]
        permission1.permission_allowed = False
        permission1.save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        # Over flag limit, blacklisted
        self.assertFalse(self.test_exam1.approved)
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        permission1.permission_allowed = True
        permission1.save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        # Over flag limit, not blacklisted after being blacklisted
        self.assertFalse(self.test_exam1.approved)
        exam_flag_list[0].resolved = True
        exam_flag_list[0].save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        # Under flag limit after being over, not blacklisted
        self.assertTrue(self.test_exam1.approved)
        permission1.permission_allowed = False
        permission1.save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        # Under flag limit, blacklisted
        self.assertFalse(self.test_exam1.approved)
        exam_flag_list[0].resolved = False
        exam_flag_list[0].save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        # Over flag limit, blacklisted
        self.assertFalse(self.test_exam1.approved)
        exam_flag_list[0].resolved = True
        exam_flag_list[0].save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        # Under flag limit after being over, blacklisted
        self.assertFalse(self.test_exam1.approved)
        permission1.permission_allowed = True
        permission1.save()
        self.test_exam1 = Exam.objects.get(pk=self.test_exam1.pk)
        # Under flag limit, not blacklisted
        self.assertTrue(self.test_exam1.approved)
