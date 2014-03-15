from chosen import forms as chosen_forms
from django import forms

from quark.base.fields import VisualSplitDateTimeField
from quark.base.forms import ChosenTermMixin
from quark.events.models import Event
from quark.events.models import EventSignUp
from quark.project_reports.models import ProjectReport
from quark.shortcuts import get_object_or_none
from quark.user_profiles.fields import UserCommonNameChoiceField


class EventForm(ChosenTermMixin, forms.ModelForm):
    start_datetime = VisualSplitDateTimeField(label='Start date and time')
    end_datetime = VisualSplitDateTimeField(label='End date and time')

    needs_pr = forms.BooleanField(
        label='Needs project report', initial=True, required=False)

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
        # If there is an event instance for this form, infer whether a project
        # report is needed based on whether the existing event has a project
        # report:
        if self.instance:
            self.fields['needs_pr'].initial = bool(self.instance.project_report)

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
            event.save(update_fields=['project_report'])
        elif event.project_report is not None:
            # Event does not need project report, so delete PR after removing
            # the foreign key from the event.
            project_report = event.project_report
            event.project_report = None
            event.save(update_fields=['project_report'])
            project_report.delete()
        return event


class EventSignUpForm(forms.ModelForm):
    # Override the driving field to prevent users from using integer values
    # that are too large:
    driving = forms.IntegerField(
        min_value=0, max_value=100, initial=0,
        label='How many people fit in your car, including yourself '
              '(0 if not driving)')
    event = None
    user = None

    class Meta(object):
        model = EventSignUp
        fields = ('comments', 'driving', 'num_guests')
        widgets = {
            # Make the comments widget shorter than the standard Textarea,
            # since signup comments typically need not be very long.
            'comments': forms.Textarea(attrs={'rows': 4})
        }

    def __init__(self, event, *args, **kwargs):
        self.event = event
        self.user = kwargs.pop('user', None)
        super(EventSignUpForm, self).__init__(*args, **kwargs)

        max_guests = self.event.max_guests_per_person
        if max_guests:
            self.fields['num_guests'] = forms.IntegerField(
                min_value=0, max_value=max_guests, initial=0,
                label='Number of guests you are bringing (up to {})'.format(
                    max_guests))
        else:
            # Hide the num_guests field from the form
            self.fields['num_guests'].widget = forms.HiddenInput()

        if not self.event.needs_drivers:
            # Hide the driving field if the event doesn't need drivers
            self.fields['driving'].widget = forms.HiddenInput()

    def clean(self):
        """Check the signup limit has not been exceeded."""
        # pylint: disable=w0201
        cleaned_data = super(EventSignUpForm, self).clean()
        num_guests = cleaned_data.get('num_guests')
        num_rsvps = self.event.get_num_rsvps()

        # Get the previous signup if it exists
        if self.user.is_authenticated():
            signup = get_object_or_none(
                EventSignUp, event=self.event, user=self.user)
        else:
            signup = get_object_or_none(
                EventSignUp, event=self.event, email=cleaned_data.get('email'))

        # If the user has signed up previously and not unsigned up, subtract
        # the user and the number of guests from the total number of rsvps
        if signup and not signup.unsignup:
            num_rsvps -= (1 + signup.num_guests)

        # Add the user and the number of guests to the total number of rsvps
        # and check that it is less than the signup limit if the limit is not
        # zero (a limit of zero implies unlimited signups)
        if self.event.signup_limit != 0:
            if (1 + num_guests + num_rsvps) > self.event.signup_limit:
                raise forms.ValidationError('There are not enough spots left.')

        # Only save a new object if a signup does not already exist for this
        # user. Otherwise, just update the existing object.
        if signup:
            self.instance = signup

        self.instance.event = self.event
        self.instance.unsignup = False
        if self.user.is_authenticated():
            self.instance.user = self.user
        return cleaned_data


class EventSignUpAnonymousForm(EventSignUpForm):
    # TODO(sjdemartini): check that the email address used does not belong to
    # a user in the database already, in which case they should be told to
    # sign in instead
    class Meta(EventSignUpForm.Meta):
        fields = ('name', 'email', 'comments', 'driving', 'num_guests')

    def __init__(self, event, *args, **kwargs):
        super(EventSignUpAnonymousForm, self).__init__(event, *args, **kwargs)
        self.fields['name'].required = True
        self.fields['email'].required = True
