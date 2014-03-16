from django.db import models
from django.conf import settings
from uuidfield import UUIDField

from quark.base.models import Term


class Poll(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(
        help_text='(e.g. characteristics/achievements honored by this award)')
    instructions = models.TextField(
        help_text='(e.g. must vote for one male and one female candidate)',
        blank=True)
    max_votes_per_user = models.PositiveSmallIntegerField(
        default=1, help_text='Maximum number of votes each user may cast')
    vote_reason_required = models.BooleanField(
        default=True,
        help_text='Must voters provide an explanation for each vote?')
    eligible_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        help_text='Whom will people be able to vote for?',
        related_name='vote_poll_eligible_users')
    start_datetime = models.DateTimeField(
        help_text='Date and time poll opens for voting')
    end_datetime = models.DateTimeField(
        help_text='Date and time poll closes')
    term = models.ForeignKey(Term)

    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        editable=False,
        related_name='vote_poll_creator')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '{name} ({term})'.format(
            name=self.name, term=self.term)


class Vote(models.Model):
    # Use a randomly-generated UUIDField for the primary key, making it
    # impossible to associate a Vote with a VoteReceipt
    id = UUIDField(auto=True, primary_key=True)
    poll = models.ForeignKey(Poll)
    nominee = models.ForeignKey(settings.AUTH_USER_MODEL)
    reason = models.TextField()

    def __unicode__(self):
        return 'Vote for {nominee} for {name} ({term})'.format(
            nominee=self.nominee, name=self.poll.name, term=self.poll.term)


class VoteReceipt(models.Model):
    # Use a randomly-generated UUIDField for the primary key, making it
    # impossible to associate a Vote with a VoteReceipt
    id = UUIDField(auto=True, primary_key=True)
    poll = models.ForeignKey(Poll)
    voter = models.ForeignKey(settings.AUTH_USER_MODEL)
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '{voter} voted at {time} for {name} ({term})'.format(
            voter=self.voter, time=self.created, name=self.poll.name,
            term=self.poll.term)
