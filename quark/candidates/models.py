import os

from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models
from django.db.models import Sum

from quark.base.models import Term
from quark.events.models import Event
from quark.events.models import EventType
from quark.exams.models import Exam
from quark.resumes.models import Resume


class Candidate(models.Model):
    """A candidate for a given term.

    Provides an interface for each candidate's progress, but
    only for a single term. To account for past progress, one will
    have to query multiple Candidate objects.
    """
    PHOTOS_LOCATION = 'candidates'

    def rename_photo(instance, filename):
        """Rename the photo to the candidate's username, and update the photo
        if it already exists.
        """
        # pylint: disable=E0213
        file_ext = os.path.splitext(filename)[1]
        filename = os.path.join(Candidate.PHOTOS_LOCATION,
                                str(instance.user.get_username()) + file_ext)
        full_path = os.path.join(settings.MEDIA_ROOT, filename)
        # if photo already exists, delete it so the new photo can use the
        # same name
        if os.path.exists(full_path):
            os.remove(full_path)
        return filename

    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    term = models.ForeignKey(Term)
    initiated = models.BooleanField(default=False)
    photo = models.ImageField(blank=True, upload_to=rename_photo)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta(object):
        ordering = ('-term', 'user__userprofile')
        permissions = (
            ('can_initiate_candidates', 'Can mark candidates as initiated'),
        )
        unique_together = ('user', 'term')

    def get_progress(self, requirement_type=None):
        """Return a dictionary with keys "completed" and "required", which
        map to the number of completed requirements and the number that were
        required, respectively.

        If requirement_type is not specified, the method returns total progress
        for all requirements. If requirement is specified, only progress for
        the specific requirement type is returned.

        Useful for summary info, progress bars, and other visualizations.
        """
        if requirement_type is None:
            requirements = CandidateRequirement.objects.filter(term=self.term)
        else:
            requirements = CandidateRequirement.objects.filter(
                term=self.term, requirement_type=requirement_type)

        # Select-related to improve performance, fetching data for requirements
        # from multiple tables
        requirements.select_related(
            'eventcandidaterequirement',
            'eventcandidaterequirement__event_type',
            'challengecandidaterequirement',
            'challengecandidaterequirement__challenge_type',
            'examfilecandidaterequirement')

        # TODO(sjdemartini): Figure out a way to optimize fetching the progress
        # for event requirements and fetching CandidateRequirementProgress
        # objects in order to minimize number of queries

        progress = [req.get_progress(self) for req in requirements]
        completed = sum([x['completed'] for x in progress])
        required = sum([x['required'] for x in progress])
        return {'completed': completed, 'required': required}

    def are_electives_required(self):
        """Return true if elective events are required; false otherwise."""
        event_reqs = CandidateRequirement.objects.filter(
            term=self.term,
            requirement_type=CandidateRequirement.EVENT)
        try:
            elective_req = event_reqs.get(
                eventcandidaterequirement__event_type__name='Elective')
        except self.DoesNotExist:
            return False
        return elective_req.get_progress(self)['required'] > 0

    def __unicode__(self):
        return '{user} ({term})'.format(user=self.user, term=self.term)


def candidate_post_save(sender, instance, created, **kwargs):
    """Ensure that a StudentOrgUserProfile exists for every Candidate,
    update the profile's 'initiation_term' field, and add the candidate to the
    appropriate group.

    If the candidate is marked as initiated, add the candidate to the Member
    group and remove the candidate from the Current Candidate group.
    If the candidate is marked as not initiated, remove the candidate from the
    Member group and add the candidate to the Current Candidate group if the
    candidate is initiating in the current term.

    Anyone who is a candidate in the student organization also needs a user
    profile as a student participating in that organization.

    The field in StudentOrgUserProfile is updated in two scenarios:
        - if Candidate marks the user as initiated.
        - if Candidate marks the user as _not_ initiated and
          StudentOrgUserProfile had recorded the user as initiated in the term
          corresponding to this Candidate object (in which case,
          StudentOrgUserProfile should now reflect that the user did not
          initiate)
    """
    # Avoid circular dependency by importing here:
    from quark.user_profiles.models import StudentOrgUserProfile

    student_org_profile, _ = StudentOrgUserProfile.objects.get_or_create(
        user=instance.user)

    candidate_group = Group.objects.get(name='Current Candidate')
    member_group = Group.objects.get(name='Member')

    if instance.initiated:
        student_org_profile.initiation_term = instance.term
        student_org_profile.save()
        instance.user.groups.add(member_group)
        instance.user.groups.remove(candidate_group)
    else:
        if student_org_profile.initiation_term == instance.term:
            student_org_profile.initiation_term = None
            student_org_profile.save()
        instance.user.groups.remove(member_group)
        if instance.term == Term.objects.get_current_term():
            instance.user.groups.add(candidate_group)
        else:
            instance.user.groups.remove(candidate_group)

models.signals.post_save.connect(candidate_post_save, sender=Candidate)


class ChallengeTypeManager(models.Manager):
    def get_by_natural_key(self, name):
        try:
            return self.get(name=name)
        except ChallengeType.DoesNotExist:
            return None


class ChallengeType(models.Model):
    name = models.CharField(max_length=60, unique=True)

    objects = ChallengeTypeManager()

    def __unicode__(self):
        return self.name

    def natural_key(self):
        return (self.name,)


class Challenge(models.Model):
    """A challenge done by a Candidate.

    Challenges are requested by the Candidate upon completion and verified by
    the person who gave the candidate the challenge.
    """
    # Custom displays for the verified NullBooleanField
    VERIFIED_CHOICES = (
        (None, 'Pending'),
        (True, 'Approved'),
        (False, 'Denied'),
    )

    candidate = models.ForeignKey(Candidate)
    challenge_type = models.ForeignKey(ChallengeType)
    description = models.CharField(max_length=255)
    verifying_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        help_text='Person who verified the challenge.')
    verified = models.NullBooleanField(choices=VERIFIED_CHOICES)
    reason = models.CharField(
        blank=True, max_length=255,
        help_text='Why is the challenge being approved or denied? (Optional)')

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '{candidate}: Challenge given by {user}'.format(
            candidate=self.candidate, user=self.verifying_user)

    class Meta(object):
        ordering = ('candidate', 'created')


class CandidateRequirement(models.Model):
    """A base for other requirements."""
    # Requirement Type constants
    EVENT = 'event'
    CHALLENGE = 'challenge'
    EXAM_FILE = 'exam'
    RESUME = 'resume'
    MANUAL = 'manual'

    REQUIREMENT_TYPE_CHOICES = (
        (EVENT, 'Event'),
        (CHALLENGE, 'Challenge'),
        (EXAM_FILE, 'Exam File'),
        (RESUME, 'Resume'),
        (MANUAL, 'Other (manually verified)')
    )

    requirement_type = models.CharField(
        max_length=9, choices=REQUIREMENT_TYPE_CHOICES, db_index=True)
    credits_needed = models.IntegerField(
        help_text='Amount of credits needed to fulfill a candidate requirement')
    term = models.ForeignKey(Term)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def get_progress(self, candidate):
        """Return a dictionary with keys "completed" and "required", which
        map to the number of completed requirements and the number that were
        required, respectively, for the given candidate.
        """
        required = self.credits_needed

        if self.requirement_type == CandidateRequirement.EVENT:
            completed = self.eventcandidaterequirement.get_completed(candidate)
        elif self.requirement_type == CandidateRequirement.CHALLENGE:
            completed = self.challengecandidaterequirement.get_completed(
                candidate)
        elif self.requirement_type == CandidateRequirement.EXAM_FILE:
            completed = self.examfilecandidaterequirement.get_completed(
                candidate)
        elif self.requirement_type == CandidateRequirement.RESUME:
            completed = self.resumecandidaterequirement.get_completed(candidate)
        elif self.requirement_type == CandidateRequirement.MANUAL:
            # Actual credits earned is read from CandidateProgress below
            completed = 0
        else:
            raise NotImplementedError(
                'Unknown type {}'.format(self.requirement_type))

        # Check per-candidate overrides and exemptions
        try:
            progress = CandidateRequirementProgress.objects.get(
                candidate=candidate, requirement=self)
            completed += progress.manually_recorded_credits
            required = progress.alternate_credits_needed
        except CandidateRequirementProgress.DoesNotExist:
            pass

        return {'completed': completed, 'required': required}

    def get_name(self):
        """Return a name for the requirement based on the requirement type."""
        if self.requirement_type == CandidateRequirement.EVENT:
            return self.eventcandidaterequirement.event_type.name
        elif self.requirement_type == CandidateRequirement.CHALLENGE:
            return self.challengecandidaterequirement.challenge_type.name
        elif self.requirement_type == CandidateRequirement.EXAM_FILE:
            return 'Uploaded Exam Files'
        elif self.requirement_type == CandidateRequirement.RESUME:
            return 'Uploaded Resume'
        elif self.requirement_type == CandidateRequirement.MANUAL:
            return self.manualcandidaterequirement.name
        else:
            raise NotImplementedError(
                'Unknown type {}'.format(self.requirement_type))

    def __unicode__(self):
        return '{req_type}, {credits} required ({term})'.format(
            req_type=self.get_requirement_type_display(),
            credits=self.credits_needed, term=self.term)

    class Meta(object):
        ordering = ('-term', 'requirement_type')


class EventCandidateRequirement(CandidateRequirement):
    """Requirement for attending events of a certain type."""
    event_type = models.ForeignKey(EventType)

    def save(self, *args, **kwargs):
        """Override save handler to ensure that requirement_type is correct."""
        self.requirement_type = CandidateRequirement.EVENT
        super(EventCandidateRequirement, self).save(*args, **kwargs)

    def get_completed(self, candidate):
        """Return the number of credits completed by candidate."""
        events_attended = Event.objects.filter(
            eventattendance__user=candidate.user,
            term=candidate.term,
            event_type=self.event_type)
        return events_attended.aggregate(
            total=Sum('requirements_credit'))['total'] or 0

    def __unicode__(self):
        return '{event_type} {req}'.format(
            event_type=self.event_type.name,
            req=super(EventCandidateRequirement, self).__unicode__())

    class Meta(object):
        ordering = ('-term', 'requirement_type', 'event_type__name')


class ChallengeCandidateRequirement(CandidateRequirement):
    """Requirement for completing challenges issued by officers."""
    challenge_type = models.ForeignKey(ChallengeType)

    def save(self, *args, **kwargs):
        """Override save handler to ensure that requirement_type is correct."""
        self.requirement_type = CandidateRequirement.CHALLENGE
        super(ChallengeCandidateRequirement, self).save(*args, **kwargs)

    def get_completed(self, candidate):
        """Return the number of credits completed by candidate."""
        return Challenge.objects.filter(
            candidate=candidate,
            challenge_type=self.challenge_type,
            verified=True).count()

    def __unicode__(self):
        return '{challenge_type} {req}'.format(
            challenge_type=self.challenge_type.name,
            req=super(ChallengeCandidateRequirement, self).__unicode__())

    class Meta(object):
        ordering = ('-term', 'requirement_type', 'challenge_type__name')


class ExamFileCandidateRequirement(CandidateRequirement):
    """Requirement for uploading exam files to the site."""
    def save(self, *args, **kwargs):
        """Override save handler to ensure that requirement_type is correct."""
        self.requirement_type = CandidateRequirement.EXAM_FILE
        super(ExamFileCandidateRequirement, self).save(*args, **kwargs)

    def get_completed(self, candidate):
        """Returns the number of credits completed by candidate"""
        return Exam.objects.get_approved().filter(
            submitter=candidate.user).count()


class ResumeCandidateRequirement(CandidateRequirement):
    """Requirement for uploading a resume to the site."""
    def save(self, *args, **kwargs):
        """Override save handler to ensure that requirement_type is correct."""
        self.requirement_type = CandidateRequirement.RESUME
        super(ResumeCandidateRequirement, self).save(*args, **kwargs)

    def get_completed(self, candidate):
        return Resume.objects.filter(user=candidate.user, verified=True).count()


class ManualCandidateRequirement(CandidateRequirement):
    name = models.CharField(max_length=60, db_index=True)

    def save(self, *args, **kwargs):
        """Override save handler to ensure that requirement_type is correct."""
        self.requirement_type = CandidateRequirement.MANUAL
        super(ManualCandidateRequirement, self).save(*args, **kwargs)

    def __unicode__(self):
        return '{name}, {credits} required ({term})'.format(
            name=self.name, credits=self.credits_needed, term=self.term)

    class Meta(object):
        ordering = ('-term', 'requirement_type', 'name')


class CandidateRequirementProgress(models.Model):
    """Track one candidate's progress towards one requirement.

    For MANUAL requirements, the manually_recorded_credits field is set
    manually. For EVENT and other auto requirements, both the
    manually_recorded_credits and the alternate_credits_needed fields may be
    used as manual adjustments.
    """
    candidate = models.ForeignKey(Candidate)
    requirement = models.ForeignKey(CandidateRequirement)
    manually_recorded_credits = models.IntegerField(
        default=0, help_text='Additional credits that go toward fulfilling a '
        'candidate requirement')
    alternate_credits_needed = models.IntegerField(
        default=0, help_text='Alternate amount of credits needed to fulfill a '
        'candidate requirement')
    comments = models.TextField(blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '{candidate}: {req}'.format(
            candidate=self.candidate, req=self.requirement)

    class Meta(object):
        ordering = ('requirement', 'candidate')
        verbose_name_plural = 'candidate requirement progresses'
