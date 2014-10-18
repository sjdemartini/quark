from django import forms
from django.contrib.auth import get_user_model

from quark.base.fields import VisualSplitDateTimeField
from quark.base.forms import ChosenTermMixin
from quark.user_profiles.fields import UserCommonNameChoiceField
from quark.user_profiles.fields import UserCommonNameMultipleChoiceField
from quark.vote.models import Poll
from quark.vote.models import Vote
from quark.vote.models import VoteReceipt


class PollForm(ChosenTermMixin, forms.ModelForm):
    """A form that is used to create polls.

    Description of Groups:

    CANDIDATES: Current candidates.
    ALL_MEMBERS: All currently initiated members (officers included).
    NON_OFFICER_MEMBERS: All members who are not currently officers.
    OFFICERS: All current officers, excluding advisors and faculty.
    CUSTOM: Creator manually selects users that are eligible.
    """

    # Group Constants
    ALL_MEMBERS = 'All Members'
    OFFICERS = 'Officers'
    CANDIDATES = 'Candidates'
    NON_OFFICER_MEMBERS = 'Non-Officer Members'
    CUSTOM = 'Custom'

    # Group Choices
    GROUPS = (
        (ALL_MEMBERS, 'All Members'),
        (OFFICERS, 'Officers'),
        (CANDIDATES, 'Candidates'),
        (NON_OFFICER_MEMBERS, 'Non-Officer Members'),
        (CUSTOM, 'Custom'),
    )

    eligible_group = forms.ChoiceField(
        choices=GROUPS,
        help_text='Which group of users will people be able to vote for?')
    eligible_users = UserCommonNameMultipleChoiceField(
        required=False,
        help_text='Whom will people be able to vote for?')
    max_votes_per_user = forms.IntegerField(min_value=1)
    start_datetime = VisualSplitDateTimeField(
        label='Date and time poll opens for voting')
    end_datetime = VisualSplitDateTimeField(
        label='Date and time poll closes')

    class Meta(object):
        model = Poll
        fields = ('name', 'description', 'instructions', 'max_votes_per_user',
                  'vote_reason_required', 'eligible_group', 'eligible_users',
                  'start_datetime', 'end_datetime', 'term')

    def get_eligible_users(self):
        eligible_group = self.cleaned_data.get('eligible_group')
        term = self.cleaned_data['term']

        if eligible_group == self.CANDIDATES:
            return get_user_model().objects.filter(
                candidate__term=term)
        if eligible_group == self.ALL_MEMBERS:
            return get_user_model().objects.filter(
                studentorguserprofile__initiation_term__isnull=False)
        if eligible_group == self.NON_OFFICER_MEMBERS:
            return get_user_model().objects.exclude(
                studentorguserprofile__initiation_term__isnull=True).exclude(
                officer__term=term)
        if eligible_group == self.OFFICERS:
            return get_user_model().objects.filter(
                officer__term=term).exclude(
                officer__position__short_name__in=[
                    'advisor', 'faculty'])

    def clean(self):
        cleaned_data = super(PollForm, self).clean()
        start = cleaned_data.get('start_datetime')
        end = cleaned_data.get('end_datetime')
        eligible_group = cleaned_data.get('eligible_group')
        eligible_users = cleaned_data.get('eligible_users')

        if start >= end:
            raise forms.ValidationError(
                'Polls must close after they open for voting.')

        if eligible_group == self.CUSTOM and not eligible_users:
            raise forms.ValidationError(
                'You must select eligible users if eligible group is Custom.')

        return cleaned_data

    def save(self, *args, **kwargs):
        eligible_group = self.cleaned_data.get('eligible_group')
        instance = super(PollForm, self).save(*args, **kwargs)

        if eligible_group != self.CUSTOM:
            eligible_users = list(self.get_eligible_users())
            self.instance.eligible_users.add(*eligible_users)

        return instance


class VoteForm(forms.ModelForm):
    """Form for voting on a poll."""
    class Meta(object):
        model = Vote
        fields = ('nominee', 'reason')

    def __init__(self, *args, **kwargs):
        self.poll = kwargs.pop('poll', None)
        self.user = kwargs.pop('user', None)
        super(VoteForm, self).__init__(*args, **kwargs)
        self.fields['nominee'] = UserCommonNameChoiceField(
            label='Nominee',
            queryset=get_user_model().objects.filter(
                pk__in=self.poll.eligible_users.values('pk')))

    def clean(self):
        cleaned_data = super(VoteForm, self).clean()
        num_votes = VoteReceipt.objects.filter(
            poll=self.poll).filter(
            voter=self.user).count()
        if num_votes >= self.poll.max_votes_per_user:
            raise forms.ValidationError(
                'You have already voted the maximum number of times')
        VoteReceipt.objects.create(poll=self.poll, voter=self.user)
        return cleaned_data

    def save(self, *args, **kwargs):
        self.instance.poll = self.poll
        return super(VoteForm, self).save(*args, **kwargs)
