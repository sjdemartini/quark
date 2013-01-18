from django.db import models

from quark.auth.models import User
from quark.base.models import Officer
from quark.base.models import Term
from quark.events.models import EventAttendance
from quark.events.models import EventType


class Candidate(models.Model):
    """
    A candidate for a given term.

    Provides an interface for each candidate's progress, but
    only for a single term. To account for past progress, one will
    have to query multiple Candidate objects.
    """
    user = models.ForeignKey(User, unique=True)
    term = models.ForeignKey(Term)
    initiated = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'%s (%s)' % (self.user, self.term)

    class Meta:
        ordering = ('-term', 'user')

    def get_progress(self, requirement_type):
        """
        Returns a tuple (#completed, #required) for a given requirement type.

        Useful for progress bars and other visualizations.
        """
        requirements = CandidateRequirement.objects.filter(
            term=self.term, requirement_type=requirement_type)
        progress = [req.get_progress(self) for req in requirements]
        completed = sum([x[0] for x in progress])
        required = sum([x[1] for x in progress])

        return (completed, required)


class Challenge(models.Model):
    """
    A challenge done by a Candidate.

    Challenges are requested by the Candidate upon completion
    and verified by the Officer who gave it.
    """
    INDIVIDUAL = 1
    GROUP = 2
    TYPES = (
        (INDIVIDUAL, 'Individual'),
        (GROUP, 'Group'))

    candidate = models.ForeignKey(Candidate)
    challenge_type = models.PositiveSmallIntegerField(choices=TYPES,
                                                      default=INDIVIDUAL)
    description = models.CharField(max_length=255)
    officer = models.ForeignKey(Officer)
    verified = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'%s: Challenge given by %s' % (self.candidate, self.officer)

    class Meta:
        ordering = ('candidate', 'updated')


class CandidateRequirement(models.Model):
    """A requirement for a given term."""
    EVENT = 1
    MANUAL = 2
    CHALLENGE = 3
    EXAM_FILE = 4
    RESUME = 5
    TYPES = (
        (EVENT, 'Event'),
        (CHALLENGE, 'Challenge'),
        (EXAM_FILE, 'Exam File'),
        (RESUME, 'Resume'),
        (MANUAL, 'Other (manually verified)'))

    name = models.CharField(max_length=60, db_index=True)
    requirement_type = models.PositiveSmallIntegerField(choices=TYPES,
                                                        db_index=True)
    credits_needed = models.IntegerField()
    term = models.ForeignKey(Term)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def get_progress(self, candidate):
        """Returns a tuple (#completed, #required) for the given candidate"""
        required = self.credits_needed

        if (self.requirement_type == CandidateRequirement.EVENT):
            # pylint: disable=E1101
            completed = self.eventcandidaterequirement.get_completed(candidate)
        elif (self.requirement_type == CandidateRequirement.MANUAL):
            # Actual credits earned is read from CandidateProgress below
            completed = 0
        elif (self.requirement_type == CandidateRequirement.CHALLENGE):
            # pylint: disable=E1101
            completed = self.challengecandidaterequirement.get_completed(
                candidate)
        elif (self.requirement_type == CandidateRequirement.EXAM_FILE):
            # TODO (wangj) requires exam files, this is just a placeholder
            completed = 0
        elif (self.requirement_type == CandidateRequirement.RESUME):
            # TODO (wangj) requires resumes, this is just a placeholder
            completed = 0
        else:
            raise NotImplementedError('Unknown type %d' % self.requirement_type)

        # Check per-candidate overrides and exemptions
        try:
            progress = CandidateProgress.objects.get(candidate=candidate,
                                                     requirement=self)
            completed += progress.credits_earned
            required -= progress.credits_exempted
        except CandidateProgress.DoesNotExist:
            pass

        return (completed, required)

    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.term)

    class Meta:
        ordering = ('-term', 'requirement_type', 'name')
        unique_together = ('name', 'term')


class EventCandidateRequirement(CandidateRequirement):
    event_type = models.ForeignKey(EventType)

    def save(self, *args, **kwargs):
        """Override save handler to ensure that requirement_type is correct"""
        self.requirement_type = CandidateRequirement.EVENT
        super(EventCandidateRequirement, self).save(*args, **kwargs)

    def get_completed(self, candidate):
        """Returns the number of credits completed by candidate"""
        events_attended = EventAttendance.objects.filter(
            person=candidate.user,
            event__term=candidate.term,
            event__event_type=self.event_type)
        return sum([e.event.requirements_credit for e in events_attended])


class ChallengeCandidateRequirement(CandidateRequirement):
    challenge_type = models.PositiveSmallIntegerField(choices=Challenge.TYPES)

    def save(self, *args, **kwargs):
        """Override save handler to ensure that requirement_type is correct"""
        self.requirement_type = CandidateRequirement.CHALLENGE
        super(ChallengeCandidateRequirement, self).save(*args, **kwargs)

    def get_completed(self, candidate):
        """Returns the number of credits completed by candidate"""
        return Challenge.objects.filter(
            candidate=candidate,
            challenge_type=self.challenge_type,
            verified=True).count()


class CandidateProgress(models.Model):
    """
    Tracks one candidate's progress towards one requirement.

    For MANUAL requirements, the credits_earned field is set manually.
    For EVENT and other auto requirements, both credits_earned and
    credits_exempted field may be used as manual adjustments.
    """
    candidate = models.ForeignKey(Candidate)
    requirement = models.ForeignKey(CandidateRequirement)
    credits_earned = models.IntegerField(default=0)
    credits_exempted = models.IntegerField(default=0)
    comments = models.TextField()

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'%s: %s' % (self.candidate, self.requirement)

    class Meta:
        ordering = ('candidate', 'requirement')
