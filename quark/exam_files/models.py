import os
import uuid

from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete
from django.db.models.signals import post_init
from django.db.models.signals import post_save

from quark.auth.models import User
from quark.courses.models import CourseInstance
from quark.courses.models import Instructor


class Exam(models.Model):
    # Exam constants
    UNKNOWN = 'un'
    MT1 = 'mt1'
    MT2 = 'mt2'
    MT3 = 'mt3'
    MT4 = 'mt4'
    FINAL = 'final'

    EXAM_CHOICES = (
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

    def rename_file(instance, filename):
        """Files are stored in directories inside the exam files directory
        corresponding to the first two characters of the unique id. File names
        consist of the whole unique 32-character alphanumeric id,
        without hyphens.
        """
        # TODO(ericdwang): look into using django-filer
        # pylint: disable=E0213
        instance.file_ext = os.path.splitext(filename)[1]
        return os.path.join(Exam.EXAM_FILES_LOCATION,
                            instance.unique_id[0:2],
                            instance.unique_id + instance.file_ext)

    # TODO(ericdwang): switch from approved to verified, adjust queries
    course_instance = models.ForeignKey(CourseInstance)
    submitter = models.ForeignKey(User, null=True, blank=True)
    exam = models.CharField(max_length=5, choices=EXAM_CHOICES)
    exam_type = models.CharField(max_length=4, choices=EXAM_TYPE_CHOICES)
    unique_id = models.CharField(max_length=32, unique=True)
    file_ext = models.CharField(max_length=5)  # includes the period
    approved = models.BooleanField(default=False)
    flags = models.PositiveSmallIntegerField(default=0)
    blacklisted = models.BooleanField(default=False)
    exam_file = models.FileField(upload_to=rename_file)

    def get_department(self):
        return self.course_instance.course.department

    def get_number(self):
        return self.course_instance.course.number

    def get_term(self):
        return self.course_instance.term.term

    def get_year(self):
        return self.course_instance.term.year

    def get_instructors(self):
        """Return a QuerySet of all instructors."""
        return self.course_instance.instructors.all()

    def get_permissions(self):
        """Return a QuerySet of all instructor permissions."""
        return InstructorPermission.objects.filter(
            instructor__in=self.get_instructors())

    def has_permission(self):
        """Return whether this exam has permission from all instructors
        associated with it.
        """
        instructors = self.course_instance.instructors.all()
        return not InstructorPermission.objects.filter(
            instructor__in=instructors, permission_allowed=False).exists()

    def get_term_name(self):
        """Return a human-readable representation of the exam's term."""
        return self.course_instance.term.verbose_name()

    def get_absolute_pathname(self):
        """Return the absolute path of the exam file."""
        return os.path.join(settings.MEDIA_ROOT, Exam.EXAM_FILES_LOCATION,
                            str(self.unique_id)[0:2],
                            self.unique_id + self.file_ext)

    def __unicode__(self):
        """Return a human-readable representation of the exam file."""
        return '{course}-{term}-{exam}-{instructors}-{exam_type}{ext}'.format(
            course=self.course_instance.course.get_url_name(),
            term=self.course_instance.term.get_url_name(), exam=self.exam,
            instructors='_'.join(
                [i.last_name for i in self.get_instructors()]),
            exam_type=self.exam_type, ext=self.file_ext)


class ExamFlag(models.Model):
    # Constant for how many times an exam can be flagged before being hidden
    LIMIT = 2

    exam = models.ForeignKey(Exam)
    reason = models.TextField(blank=False)
    created = models.DateTimeField(auto_now_add=True)
    # After flagged exam is dealt with, an explanation about how it was
    # resolved should be added, and then it should be de-flagged
    resolution = models.TextField(blank=True)
    resolved = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return unicode(self.exam) + ' Flag'


class InstructorPermission(models.Model):
    instructor = models.OneToOneField(Instructor)
    permission_allowed = models.NullBooleanField()
    correspondence = models.TextField(blank=True)

    def __unicode__(self):
        return unicode(self.instructor) + ' Permission'


def assign_unique_id(sender, instance, **kwargs):
    """Assign a unique 32-character alphanumeric id to a newly created Exam."""
    instance.unique_id = uuid.uuid4().hex


def create_new_permissions(sender, instance, **kwargs):
    """Check if new InstructorPermissions need to be created after an exam
    is saved.
    """
    for instructor in instance.course_instance.instructors.all():
        InstructorPermission.objects.get_or_create(instructor=instructor)


def delete_file(sender, instance, **kwargs):
    """Delete an exam file after the exam has been deleted, if it exists."""
    if bool(instance.exam_file):  # check if exam file exists
        try:
            instance.exam_file.delete()
        except OSError:
            pass
    # if exam file has already been deleted, then do nothing and continue
    # with deleting the exam model


def hide_exam_limit_exceeded(sender, instance, **kwargs):
    """Hide an exam if it has been flagged more than ExamFlag.LIMIT times.
    Unhide an exam if flag has been resolved and professors aren't blacklisted.
    Also updates the amount of flags an exam has every time a flag is updated.
    """
    instance.exam.flags = ExamFlag.objects.filter(
        exam=instance.exam, resolved=False).count()
    if instance.exam.flags > ExamFlag.LIMIT:
        instance.exam.approved = False
    elif instance.exam.has_permission():
        instance.exam.approved = True
    instance.exam.save()


def hide_exam_blacklisted(sender, instance, **kwargs):
    """Hide all exams associated with a blacklisted professor.
    Unhide all unflagged exams if a professor has been unblacklisted.
    Also updates whether an exam is blacklisted every time an
    instructor permission is updated.
    """
    query = Exam.objects.filter(
        course_instance__instructors=instance.instructor)
    if instance.permission_allowed is False:
        query.exclude(approved=False, blacklisted=True).update(
            approved=False, blacklisted=True)
    else:
        query = query.filter(flags__lte=ExamFlag.LIMIT)
        for exam in query:
            if exam.has_permission():
                exam.approved = True
                exam.blacklisted = False
                exam.save()


post_init.connect(assign_unique_id, sender=Exam)
post_save.connect(create_new_permissions, sender=Exam)
post_delete.connect(delete_file, sender=Exam)
post_save.connect(hide_exam_limit_exceeded, sender=ExamFlag)
post_save.connect(hide_exam_blacklisted, sender=InstructorPermission)
