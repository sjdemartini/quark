from chosen import forms as chosen_forms
from django import forms
from django.contrib.auth import get_user_model

from quark.accounts.fields import UserCommonNameMultipleChoiceField
from quark.base.fields import VisualSplitDateTimeField
from quark.base.models import Term
# TODO(jerrycheng): import Vote and VoteReceipt once forms are made
from quark.vote.models import Poll


class PollForm(forms.ModelForm):
    """A form that is used to create polls.

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

    eligible_group = forms.ChoiceField(
        choices=GROUPS,
        help_text='Which group of users will people be able to vote for?')
    eligible_users = UserCommonNameMultipleChoiceField(
        queryset=get_user_model().objects.all(),
        required=False,
        help_text='Whom will people be able to vote for?')
    max_votes_per_user = forms.IntegerField(min_value=1)
    start_datetime = VisualSplitDateTimeField(
        label='Date and time poll opens for voting')
    end_datetime = VisualSplitDateTimeField(
        label='Date and time poll closes')

    class Meta:
        model = Poll
        fields = ('name', 'description', 'instructions', 'max_votes_per_user',
                  'vote_reason_required', 'eligible_group', 'eligible_users',
                  'start_datetime', 'end_datetime', 'term')

    def __init__(self, *args, **kwargs):
        super(PollForm, self).__init__(*args, **kwargs)
        # For fields which reference a QuerySet that must be evaluated (i.e.,
        # hits the database and isn't "lazy"), create fields in the __init__ to
        # avoid database errors in Django's test runner
        self.fields['term'] = chosen_forms.ChosenModelChoiceField(
            label='Term',
            queryset=Term.objects.get_terms(
                include_future=False, include_summer=True, reverse=False),
            initial=Term.objects.get_current_term())

    def get_eligible_users(self):
        eligible_group = self.cleaned_data.get('eligible_group')
        term = self.cleaned_data['term']

        if eligible_group == self.CANDIDATES:
            return get_user_model().objects.filter(
                candidate__term=term)
        if eligible_group == self.ALL_MEMBERS:
            return get_user_model().objects.filter(
                tbpprofile__initiation_term__isnull=False)
        if eligible_group == self.NON_OFFICER_MEMBERS:
            return get_user_model().objects.exclude(
                tbpprofile__initiation_term__isnull=True).exclude(
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

        if eligible_group == self.OTHER and not eligible_users:
            raise forms.ValidationError(
                'You must select eligible users if eligible group is Other.')

        return cleaned_data

    def save(self, *args, **kwargs):
        eligible_group = self.cleaned_data.get('eligible_group')
        instance = super(PollForm, self).save(*args, **kwargs)

        if eligible_group != self.OTHER:
            eligible_users = list(self.get_eligible_users())
            self.instance.eligible_users.add(*eligible_users)

        return instance

# TODO(jerrycheng): implement form for users to use when voting
# class VoteForm(forms.ModelForm):
#
#     class Meta:
#         model = Vote
