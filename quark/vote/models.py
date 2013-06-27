from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model

from quark.base.models import Term


class Poll(models.Model):
    """A poll for voting for users.

    Description of Groups:
    CANDIDATES: Current candidates.
    ALL_MEMBERS: All currently initiated members (officers included).
    NON_OFFICER_MEMBERS: All members who are not currently officers.
    OFFICERS: All current officers, excluding advisors and faculty.
    OTHER: Defaults to all users.
    """

    # Group Constants
    CANDIDATES = 'Candidates'
    ALL_MEMBERS = 'All Members'
    NON_OFFICER_MEMBERS = 'Members'
    OFFICERS = 'Officers'
    OTHER = 'Other'

    # Group Choices
    GROUPS = (
        (CANDIDATES, 'Candidates'),
        (ALL_MEMBERS, 'All Members'),
        (NON_OFFICER_MEMBERS, 'Members'),
        (OFFICERS, 'Officers'),
        (OTHER, 'Other'),
    )

    name = models.CharField(max_length=50)
    description = models.TextField(
        help_text='Criteria for nomination')
    instructions = models.TextField(
        help_text='Specific instructions for voters (e.g. votes per user)')
    max_votes_per_user = models.IntegerField(
        default=1, help_text='Maximum number of votes each user may cast')
    vote_reason_required = models.BooleanField(
        default=True,
        help_text='Determines if voters must provide a reason for votes')
    eligible_group = models.CharField(
        max_length=20,
        choices=GROUPS,
        help_text='Determines the user group voters can vote for')
    start_datetime = models.DateTimeField(
        help_text='Date and time poll opens for voting')
    end_datetime = models.DateTimeField(
        help_text='Date and time poll closes')
    term = models.ForeignKey(Term)

    def __unicode__(self):
        return '{award} ({term})'.format(
            award=self.award, term=self.term)

    def get_eligible_users(self):
        curr_term = Term.objects.get_current_term()
        if self.eligible_group == Poll.CANDIDATES:
            return get_user_model().objects.filter(candidate__term=curr_term)
        elif self.eligible_group == Poll.ALL_MEMBERS:
            return get_user_model().objects.filter(
                tbpprofile__initiation_term__isnull=False)
        elif self.eligible_group == Poll.NON_OFFICER_MEMBERS:
            return get_user_model().objects.exclude(
                tbpprofile__initiation_term__isnull=True).exclude(
                    officer__term=curr_term)
        elif self.eligible_group == Poll.OFFICERS:
            return get_user_model().objects.filter(
                officer__term=curr_term).exclude(
                    officer__position__short_name__in=['advisor', 'faculty'])
        else:
            return get_user_model().objects.all()


class Vote(models.Model):
    poll = models.ForeignKey(Poll)
    nominee = models.ForeignKey(settings.AUTH_USER_MODEL)
    reason = models.TextField()

    def __unicode__(self):
        return 'Vote for {nominee} for {award} ({term})'.format(
            nominee=self.nominee, award=self.poll.award, term=self.poll.term)


class VoteReceipt(models.Model):
    poll = models.ForeignKey(Poll)
    voter = models.ForeignKey(settings.AUTH_USER_MODEL)
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '{voter} voted at {time} for {award} ({term})'.format(
            voter=self.voter, time=self.created, award=self.poll.award,
            term=self.poll.term)
