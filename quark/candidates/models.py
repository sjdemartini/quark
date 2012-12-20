from django.db import models

from quark.auth.models import User
from quark.base.models import Term
from quark.events.models import EventType


class CandidateRequirement(models.Model):
    EVENT = 1
    PAYMENT = 2
    CHALLENGE = 3
    EXAM_FILE = 4
    TYPES = (
        (EVENT, 'Event'),
        (PAYMENT, 'Payment'),
        (CHALLENGE, 'Challenge'),
        (EXAM_FILE, 'Exam File'))

    name = models.CharField(max_length=60, db_index=True)
    requirement_type = models.PositiveSmallIntegerField(choices=TYPES,
                                                        db_index=True)
    credits_needed = models.IntegerField()
    term = models.ForeignKey(Term)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('-term', 'requirement_type', 'name')
        unique_together = ('name', 'term')


class EventCandidateRequirement(CandidateRequirement):
    event_type = models.ForeignKey(EventType)


class CandidateProgress(models.Model):
    user = models.ForeignKey(User)
    requirement = models.ForeignKey(CandidateRequirement)
    credits_earned = models.IntegerField()
    credits_exempted = models.IntegerField()

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'%s: %s' % (self.user, self.requirement)

    class Meta:
        ordering = ('user', 'requirement')
