import os

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import pre_delete
from django.db.models.signals import post_save
from uuidfield import UUIDField

from quark.courses.models import CourseInstance
from quark.courses.models import Instructor
from quark.shortcuts import disable_for_loaddata


class ExamManager(models.Manager):
    def get_approved(self):
        """Return a filtered queryset of approved exams.

        An exam is 'approved' if it meets all of the following conditions:
          1. Verified by an officer
          2. Is not associated with a blacklisted instructor
          3. Has less than or equal to ExamFlag.LIMIT flags
        """
        return self.filter(verified=True, blacklisted=False,
                           flags__lte=ExamFlag.LIMIT)


def generate_exam_filepath(instance, filename):
    """Generate a file name and path for the given exam file.

    Used for the Exam model's exam file upload_to function.

    Files are stored in directories inside the exam files directory
    corresponding to the first two characters of the unique id. File names
    consist of the whole unique 32-character alphanumeric id, without hyphens.
    """
    instance.file_ext = os.path.splitext(filename)[1]
    return instance.get_relative_pathname()


class Exam(models.Model):
    # Exam Number constants
    UNKNOWN = 'un'
    MT1 = 'mt1'
    MT2 = 'mt2'
    MT3 = 'mt3'
    MT4 = 'mt4'
    FINAL = 'final'

    EXAM_NUMBER_CHOICES = (
        (UNKNOWN, 'Unknown'),
        (MT1, 'Midterm 1'),
        (MT2, 'Midterm 2'),
        (MT3, 'Midterm 3'),
        (MT4, 'Midterm 4'),
        (FINAL, 'Final'),
    )

    # Exam Type constants
    EXAM = 'exam'
    SOLN = 'soln'

    EXAM_TYPE_CHOICES = (
        (EXAM, 'Exam'),
        (SOLN, 'Solution'),
    )

    # Constants
    EXAM_FILES_LOCATION = 'exam_files'

    course_instance = models.ForeignKey(CourseInstance)
    submitter = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                                  blank=True)
    exam_number = models.CharField(max_length=5, choices=EXAM_NUMBER_CHOICES)
    exam_type = models.CharField(max_length=4, choices=EXAM_TYPE_CHOICES)
    unique_id = UUIDField(auto=True)
    file_ext = models.CharField(max_length=5)  # includes the period
    # The exam must be verified manually be an officer:
    verified = models.BooleanField(default=False, blank=True)
    flags = models.PositiveSmallIntegerField(default=0)
    blacklisted = models.BooleanField(default=False)
    exam_file = models.FileField(upload_to=generate_exam_filepath)

    objects = ExamManager()

    class Meta(object):
        permissions = (
            ('view_exams',
             'Can view all exams (including blacklisted and flagged exams)'),
        )

    @property
    def course(self):
        return self.course_instance.course

    @property
    def term(self):
        return self.course_instance.term

    @property
    def instructors(self):
        """Return a QuerySet of all instructors associated with the exam."""
        return self.course_instance.instructors.all()

    def is_approved(self):
        """An exam is 'approved' if it meets all of the following conditions:
          1. Verified by an officer
          2. Is not associated with a blacklisted instructor
          3. Has less than or equal to ExamFlag.LIMIT flags
        """
        return (self.verified and not self.blacklisted
                and self.flags <= ExamFlag.LIMIT)

    def has_permission(self):
        """Return whether this exam has permission from all instructors
        associated with it.
        """
        return not self.course_instance.instructors.filter(
            instructorpermission__permission_allowed=False).exists()

    def get_folder(self):
        """Return the path of the folder where the exam file is."""
        return os.path.join(
            settings.MEDIA_ROOT, Exam.EXAM_FILES_LOCATION,
            str(self.unique_id)[0:2])

    def get_relative_pathname(self):
        """Return the relative path of the exam file from inside the media
        root.
        """
        return os.path.join(Exam.EXAM_FILES_LOCATION,
                            str(self.unique_id)[0:2],
                            str(self.unique_id) + self.file_ext)

    def get_absolute_pathname(self):
        """Return the absolute path of the exam file."""
        return os.path.join(settings.MEDIA_ROOT, self.get_relative_pathname())

    def get_absolute_url(self):
        return reverse('exams:edit', args=(self.pk,))

    def get_download_file_name(self):
        """Return the file name of the exam file when it is downloaded."""
        return '{course}-{term}-{number}-{instructors}-{type}{ext}'.format(
            course=self.course_instance.course.get_url_name(),
            term=self.course_instance.term.get_url_name(),
            number=self.exam_number,
            instructors='_'.join([i.last_name for i in self.instructors]),
            type=self.exam_type,
            ext=self.file_ext)

    def __unicode__(self):
        """Return a human-readable representation of the exam file."""
        exam_unicode = '{term} {number} {type} for {course}'.format(
            term=self.course_instance.term.verbose_name(),
            number=self.get_exam_number_display(),
            type=self.get_exam_type_display(),
            course=self.course_instance.course)
        if self.instructors:
            instructors = ', '.join([i.last_name for i in self.instructors])
            return '{}, taught by {}'.format(exam_unicode, instructors)
        else:
            return '{} (Instructors Unknown)'.format(exam_unicode)


class ExamFlag(models.Model):
    """Flag an issue with a particular exam on the website."""
    # Constant for how many times an exam can be flagged before being hidden
    LIMIT = 2

    exam = models.ForeignKey(Exam, help_text='The exam that has an issue.')
    reason = models.TextField(blank=False,
                              help_text='Why is the exam being flagged?')
    created = models.DateTimeField(auto_now_add=True)
    # After flagged exam is dealt with, an explanation about how it was
    # resolved should be added, and then it should be de-flagged
    resolution = models.TextField(blank=True)
    resolved = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '{} Flag'.format(unicode(self.exam))


class InstructorPermission(models.Model):
    instructor = models.OneToOneField(Instructor)
    permission_allowed = models.BooleanField(
        help_text='Has this instructor given permission to post exams?')
    correspondence = models.TextField(
        blank=True,
        help_text='Reason for why permission was or was not given.')

    class Meta(object):
        ordering = ('instructor',)

    def __unicode__(self):
        return '{} Permission'.format(unicode(self.instructor))


def delete_file(sender, instance, **kwargs):
    """Delete an exam file after the exam has been deleted, if it exists."""
    if bool(instance.exam_file):  # check if exam file exists
        try:
            instance.exam_file.delete()
        except OSError:
            pass
    # if exam file has already been deleted, then do nothing and continue
    # with deleting the exam model


@disable_for_loaddata
def update_exam_flags(sender, instance, **kwargs):
    """Update the amount of flags an exam has every time a flag is updated."""
    exam = Exam.objects.get(pk=instance.exam.pk)
    exam.flags = ExamFlag.objects.filter(exam=exam, resolved=False).count()
    exam.save()


@disable_for_loaddata
def update_exam_blacklist(sender, instance, **kwargs):
    """Update whether an exam is blacklisted every time an instructor
    permission is updated.
    """
    exams = Exam.objects.filter(
        course_instance__instructors=instance.instructor)
    if instance.permission_allowed is False:
        exams.exclude(blacklisted=True).update(blacklisted=True)
    else:
        for exam in exams:
            if exam.has_permission():
                exam.blacklisted = False
                exam.save()


pre_delete.connect(delete_file, sender=Exam)
post_save.connect(update_exam_flags, sender=ExamFlag)
post_save.connect(update_exam_blacklist, sender=InstructorPermission)
