from django.db import models

from quark.auth.models import User
from quark.base.models import Term
from quark.courses.models import Course
from quark.courses.models import Instructor


class Survey(models.Model):
    course = models.ForeignKey(Course)
    term = models.ForeignKey(Term)
    instructor = models.ForeignKey(Instructor)
    prof_rating = models.PositiveSmallIntegerField()
    course_rating = models.PositiveSmallIntegerField()
    time_commitment = models.PositiveSmallIntegerField()
    exam_difficulty = models.PositiveSmallIntegerField(blank=True, null=True)
    hw_difficulty = models.PositiveSmallIntegerField(blank=True, null=True)
    comments = models.TextField()
    submitter = models.ForeignKey(User)
    published = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%s (%s)' % (self.course, self.submitter)

    class Meta:
        ordering = ('course', 'instructor', '-term')
