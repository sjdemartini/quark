from chosen import forms as chosen_forms
from django import forms
from django.forms.formsets import BaseFormSet
from django.forms.formsets import formset_factory

from quark.base.models import Term
from quark.candidates.models import Candidate
from quark.candidates.models import CandidateRequirement
from quark.candidates.models import Challenge
from quark.candidates.models import ChallengeCandidateRequirement
from quark.candidates.models import EventCandidateRequirement
from quark.candidates.models import ExamFileCandidateRequirement
from quark.candidates.models import ManualCandidateRequirement
from quark.events.models import EventType


class CandidatePhotoForm(forms.ModelForm):
    photo = forms.ImageField()

    class Meta:
        model = Candidate
        fields = ('photo',)


class ChallengeVerifyForm(forms.ModelForm):
    verified = forms.NullBooleanField()

    class Meta:
        model = Challenge
        fields = ('verified',)


class CandidateRequirementForm(forms.ModelForm):
    credits_needed = forms.IntegerField(
        label='', min_value=0,
        widget=forms.TextInput(attrs={'size': 2, 'maxlength': 2}))

    class Meta:
        model = CandidateRequirement
        exclude = ('requirement_type', 'term', 'created', 'updated')


class EventCandidateRequirementForm(CandidateRequirementForm):
    event_type = chosen_forms.ChosenModelChoiceField(
        label='Event type', queryset=EventType.objects.all())

    class Meta(CandidateRequirementForm.Meta):
        model = EventCandidateRequirement

    def clean(self):
        """Check for duplicate event requirements in the current term."""
        cleaned_data = super(EventCandidateRequirementForm, self).clean()
        event_type = cleaned_data.get('event_type')
        duplicates = EventCandidateRequirement.objects.filter(
            term=Term.objects.get_current_term(),
            event_type=event_type)
        if duplicates.exists():
            raise forms.ValidationError(
                'A candidate requirement for {type} events already'
                'exists.'.format(type=event_type))
        return cleaned_data


class ChallengeCandidateRequirementForm(CandidateRequirementForm):
    challenge_type = chosen_forms.ChosenChoiceField(
        label='Challenge type', choices=Challenge.CHALLENGE_TYPE_CHOICES)

    class Meta(CandidateRequirementForm.Meta):
        model = ChallengeCandidateRequirement

    def clean(self):
        """Check for duplicate challenge requirements in the current term."""
        cleaned_data = super(ChallengeCandidateRequirementForm, self).clean()
        challenge_type = cleaned_data.get('challenge_type')
        duplicates = ChallengeCandidateRequirement.objects.filter(
            term=Term.objects.get_current_term(),
            challenge_type=challenge_type)
        if duplicates.exists():
            raise forms.ValidationError(
                'A candidate requirement for {type} challenges already'
                'exists.'.format(type=challenge_type))
        return cleaned_data


class ExamFileCandidateRequirementForm(CandidateRequirementForm):
    class Meta(CandidateRequirementForm.Meta):
        model = ExamFileCandidateRequirement

    def clean(self):
        """Check for duplicate exam file requirements in the current term."""
        cleaned_data = super(ExamFileCandidateRequirementForm, self).clean()
        duplicates = ExamFileCandidateRequirement.objects.filter(
            term=Term.objects.get_current_term())
        if duplicates.exists():
            raise forms.ValidationError(
                'A candidate requirement for exam files already exists.')
        return cleaned_data


class ManualCandidateRequirementForm(CandidateRequirementForm):
    name = forms.CharField(label='Name')

    class Meta(CandidateRequirementForm.Meta):
        model = ManualCandidateRequirement


class CandidateRequirementProgressForm(forms.Form):
    manually_recorded_credits = forms.IntegerField(
        min_value=0,
        widget=forms.TextInput(attrs={'size': 2, 'maxlength': 2}),
        required=False)
    credits_needed = forms.IntegerField(
        min_value=0,
        widget=forms.TextInput(attrs={'size': 2, 'maxlength': 2}))
    comments = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}), required=False)


class BaseCandidateRequirementFormset(BaseFormSet):
    def total_form_count(self):
        """Sets the number of forms equal to the number of candidate
        requirements for the current term.
        """
        return CandidateRequirement.objects.filter(
            term=Term.objects.get_current_term()).count()


# pylint: disable=C0103
CandidateRequirementFormSet = formset_factory(
    CandidateRequirementForm,
    formset=BaseCandidateRequirementFormset)


# pylint: disable=C0103
CandidateRequirementProgressFormSet = formset_factory(
    CandidateRequirementProgressForm,
    formset=BaseCandidateRequirementFormset)
