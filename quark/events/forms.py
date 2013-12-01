from chosen import forms as chosen_forms
from django import forms

from quark.base.fields import VisualSplitDateTimeField
from quark.base.forms import ChosenTermMixin
from quark.events.models import Event
from quark.events.models import EventSignUp
from quark.project_reports.models import ProjectReport
from quark.user_profiles.fields import UserCommonNameChoiceField


class EventForm(ChosenTermMixin, forms.ModelForm):
    start_datetime = VisualSplitDateTimeField(label='Start date and time')
    end_datetime = VisualSplitDateTimeField(label='End date and time')

    needs_pr = forms.BooleanField(label='Needs project report', required=False)

    contact = UserCommonNameChoiceField()

    class Meta(object):
        model = Event
        exclude = ('cancelled', 'project_report')
        widgets = {
            'committee': chosen_forms.ChosenSelect(),
            'event_type': chosen_forms.ChosenSelect(),
            'restriction': chosen_forms.ChosenSelect()
        }

    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        self.fields['committee'].required = True

    def clean(self):
        cleaned_data = super(EventForm, self).clean()
        start_datetime = cleaned_data.get('start_datetime')
        end_datetime = cleaned_data.get('end_datetime')
        is_validation_error = False
        if not start_datetime:
            self._errors['start_datetime'] = self.error_class(
                ['Your start time is not in the proper format.'])
            is_validation_error = True
        if not end_datetime:
            self._errors['end_datetime'] = self.error_class(
                ['Your end time is not in the proper format.'])
            is_validation_error = True
        if is_validation_error:
            # If either of start or end are invalid, raise validation error
            # now, before trying comparison:
            raise forms.ValidationError('Invalid Event')

        if end_datetime < start_datetime:
            error_msg = 'Your event is scheduled to end before it starts.'
            self._errors['start_datetime'] = self.error_class([error_msg])
            self._errors['end_datetime'] = self.error_class([error_msg])
            raise forms.ValidationError('Invalid Event')
        return cleaned_data

    def save(self, *args, **kwargs):
        event = super(EventForm, self).save(*args, **kwargs)
        needs_pr = self.cleaned_data['needs_pr']

        if needs_pr:
            if event.project_report is None:
                # Create PR
                project_report = ProjectReport()
            else:
                # Update PR
                project_report = event.project_report

            project_report.term = event.term
            project_report.date = event.start_datetime.date()
            project_report.title = event.name
            project_report.author = event.contact
            project_report.committee = event.committee
            project_report.save()
            event.project_report = project_report
            event.save()
        elif event.project_report is not None:
            # Does not need project report, so delete PR
            event.project_report.delete()
            event.project_report = None
            event.save()
        return event


class EventSignUpForm(forms.ModelForm):
    class Meta(object):
        model = EventSignUp
        fields = ('name', 'comments', 'driving', 'num_guests')

    def __init__(self, *args, **kwargs):
        max_guests = kwargs.pop('max_guests', None)
        super(EventSignUpForm, self).__init__(*args, **kwargs)
        if max_guests:
            self.fields['num_guests'] = forms.IntegerField(
                min_value=0, max_value=max_guests, initial=0,
                label='Number of guests you are bringing (up to {})'.format(
                    max_guests))
        else:
            # Remove the num_guests field from the form
            del self.fields['num_guests']

    # TODO(sjdemartini): Perform separate validation to ensure that the event
    # has enough space for the user and his guests, considering whether the
    # user is editing an existing signup or creating a new signup.


class EventSignUpAnonymousForm(EventSignUpForm):
    class Meta(object):
        model = EventSignUp
        fields = ('name', 'email', 'comments', 'driving', 'num_guests')

    def __init__(self, *args, **kwargs):
        super(EventSignUpAnonymousForm, self).__init__(*args, **kwargs)
        self.fields['email'].required = True
