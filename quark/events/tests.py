import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone

from quark.base.models import Term
from quark.base_tbp.models import Officer
from quark.base_tbp.models import OfficerPosition
from quark.candidates.models import Candidate
from quark.events.forms import EventForm
from quark.events.models import Event
from quark.events.models import EventSignUp
from quark.events.models import EventType
from quark.project_reports.models import ProjectReport
from quark.shortcuts import get_object_or_none


@override_settings(USE_TZ=True)
class EventTesting(TestCase):
    """Define a common setUp and helper method for event testing.

    Subclassed below for ease of testing various aspects of events.
    """
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='bentleythebent',
            email='it@tbp.berkeley.edu',
            password='testofficerpw',
            first_name='Bentley',
            last_name='Bent')

        self.committee = OfficerPosition(
            short_name='IT',
            long_name='Information Technology',
            rank=2,
            mailing_list='IT')
        self.committee.save()

        self.term = Term(term=Term.SPRING, year=2012, current=True)
        self.term.save()

        self.event_type, _ = EventType.objects.get_or_create(
            name='Test Event Type')

    def create_event(self, start_time, end_time, name='My Test Event',
                     restriction=Event.OFFICER):
        """Create, save, and return a new event."""
        event = Event(name=name,
                      event_type=self.event_type,
                      start_datetime=start_time,
                      end_datetime=end_time,
                      term=self.term,
                      location='A test location',
                      contact=self.user,
                      committee=self.committee,
                      restriction=restriction)
        event.save()
        return event

    def assert_can_view(self, event, user):
        """Assert that the given event can be viewed by the given user."""
        self.assertTrue(
            event.can_user_view(self.user),
            'Should be able to view {} event'.format(
                event.get_restriction_display()))

    def assert_cannot_view(self, event, user):
        """Assert that the given event cannot be viewed by the given user."""
        self.assertFalse(
            event.can_user_view(self.user),
            'Should not be able to view {} event'.format(
                event.get_restriction_display()))

    def assert_can_sign_up(self, event, user):
        """Assert that the given event can be viewed by the given user."""
        self.assertTrue(
            event.can_user_sign_up(self.user),
            'Should be able to sign up for {} event'.format(
                event.get_restriction_display()))

    def assert_cannot_sign_up(self, event, user):
        """Assert that the given event can be viewed by the given user."""
        self.assertFalse(
            event.can_user_sign_up(self.user),
            'Should not be able to sign up for {} event'.format(
                event.get_restriction_display()))


class EventTest(EventTesting):
    def test_eventtype_get_by_natural_key(self):
        event_type_name = 'New Test Event Type'
        EventType(name=event_type_name).save()
        event_type = EventType.objects.get_by_natural_key(event_type_name)
        self.assertEqual(event_type.name, event_type_name)

    def test_eventtype_get_by_natural_key_does_not_exist(self):
        event_type = EventType.objects.get_by_natural_key(
            'New Test Event Type')
        self.assertIsNone(event_type)

    def test_get_upcoming(self):
        # Create an event that hasn't started yet:
        start_time = timezone.now() + datetime.timedelta(hours=2)
        end_time = start_time + datetime.timedelta(hours=3)
        event = self.create_event(start_time, end_time)
        upcoming_events = Event.objects.get_upcoming()
        self.assertIn(event, upcoming_events)

        # Make the event be set to occur in a future term
        future_term = Term(term=self.term.term, year=(self.term.year + 1),
                           current=False)
        future_term.save()
        event.term = future_term
        event.save()
        self.assertIn(
            event, Event.objects.get_upcoming(current_term_only=False))
        self.assertNotIn(
            event, Event.objects.get_upcoming(current_term_only=True))

    def test_is_upcoming(self):
        # Create an event that hasn't started yet:
        start_time = timezone.now() + datetime.timedelta(hours=2)
        end_time = start_time + datetime.timedelta(hours=3)
        event = self.create_event(start_time, end_time)
        self.assertTrue(event.is_upcoming())
        upcoming_events = Event.objects.get_upcoming()
        self.assertIn(event, upcoming_events)
        self.assertEqual(1, upcoming_events.count())

        event.cancelled = True
        event.save()
        self.assertFalse(event.is_upcoming())
        upcoming_events = Event.objects.get_upcoming()
        self.assertEqual(0, upcoming_events.count())

        # Create an event that has already started but hasn't ended yet:
        start_time = timezone.now() - datetime.timedelta(hours=2)
        end_time = timezone.now() + datetime.timedelta(hours=3)
        event = self.create_event(start_time, end_time,
                                  name='My Ongoing Event')
        self.assertTrue(event.is_upcoming())
        event.cancelled = True
        event.save()
        self.assertFalse(event.is_upcoming())

        # Create an event that has already ended:
        start_time = timezone.now() - datetime.timedelta(days=2)
        end_time = start_time + datetime.timedelta(hours=3)
        event = self.create_event(start_time, end_time,
                                  name='My Old Event')
        self.assertFalse(event.is_upcoming())
        event.cancelled = True
        event.save()
        self.assertFalse(event.is_upcoming())

    def test_is_multiday(self):
        start_time = datetime.datetime(2015, 3, 14, 9, 26, 53, 59)
        start_time = timezone.make_aware(start_time,
                                         timezone.get_current_timezone())
        end_time = start_time + datetime.timedelta(days=1)
        event = self.create_event(start_time, end_time,
                                  name='My Multiday Event')
        self.assertTrue(event.is_multiday())

        end_time = start_time + datetime.timedelta(weeks=1)
        event = self.create_event(start_time, end_time,
                                  name='My Weeklong Event')
        self.assertTrue(event.is_multiday())

        # Create a very long event that does not span more than one day
        start_time = start_time.replace(hour=0, minute=1)
        end_time = start_time + datetime.timedelta(hours=23, minutes=50)
        event = self.create_event(start_time, end_time,
                                  name='My Non-multiday Event')
        self.assertFalse(event.is_multiday())

    def test_get_user_viewable(self):
        # self.user is just an ordinary user with no groups or special
        # permissions, so they should be able to view public, open, and
        # candidate events, but not member and officer events
        start_time = timezone.now()
        end_time = start_time + datetime.timedelta(hours=2)
        event_public = self.create_event(
            start_time, end_time, restriction=Event.PUBLIC)
        event_open = self.create_event(
            start_time, end_time, restriction=Event.OPEN)
        event_candidate = self.create_event(
            start_time, end_time, restriction=Event.CANDIDATE)
        event_member = self.create_event(
            start_time, end_time, restriction=Event.MEMBER)
        event_officer = self.create_event(
            start_time, end_time, restriction=Event.OFFICER)

        visible_events = Event.objects.get_user_viewable(self.user)
        expected_events = [event_public, event_open, event_candidate]
        self.assertQuerysetEqual(visible_events,
                                 [repr(event) for event in expected_events],
                                 ordered=False)

        # Make this person a candidate, and view the permissions should stay
        # the same
        Candidate(user=self.user, term=self.term).save()
        visible_events = Event.objects.get_user_viewable(self.user)
        self.assertQuerysetEqual(visible_events,
                                 [repr(event) for event in expected_events],
                                 ordered=False)

        # Make this person an officer, and they should be able to see all
        # events
        Officer(user=self.user, position=self.committee, term=self.term).save()
        visible_events = Event.objects.get_user_viewable(self.user)
        expected_events.extend([event_member, event_officer])
        self.assertQuerysetEqual(visible_events,
                                 [repr(event) for event in expected_events],
                                 ordered=False)

        # TODO(sjdemartini): add tests for members once UserProfile.is_member
        # is not purely LDAP-dependent

    def test_can_user_view(self):
        # self.user is just an ordinary user with no groups or special
        # permissions, so they should be able to view public, open, and
        # candidate events, but not member and officer events
        restrictions = [Event.PUBLIC, Event.OPEN, Event.CANDIDATE,
                        Event.MEMBER, Event.OFFICER]

        start_time = timezone.now()
        end_time = start_time + datetime.timedelta(hours=2)
        event = self.create_event(start_time, end_time)
        for restriction in restrictions:
            event.restriction = restriction
            event.save()
            if restriction in Event.VISIBLE_TO_EVERYONE:
                self.assert_can_view(event, self.user)
            else:
                self.assert_cannot_view(event, self.user)

        # Make this person a candidate, and view the permissions should stay
        # the same
        Candidate(user=self.user, term=self.term).save()
        for restriction in restrictions:
            event.restriction = restriction
            event.save()
            if restriction in Event.VISIBLE_TO_EVERYONE:
                self.assert_can_view(event, self.user)
            else:
                self.assert_cannot_view(event, self.user)

        # Make this person an officer, and they should be able to see all
        # events
        Officer(user=self.user, position=self.committee, term=self.term).save()
        for restriction in restrictions:
            event.restriction = restriction
            event.save()
            self.assert_can_view(event, self.user)

        # TODO(sjdemartini): add tests for members once UserProfile.is_member
        # is not purely LDAP-dependent

    def test_can_user_sign_up(self):
        # self.user is just an ordinary user with no groups or special
        # permissions, so the user should only be able to sign up for public
        # events
        restrictions = [Event.PUBLIC, Event.OPEN, Event.CANDIDATE,
                        Event.MEMBER, Event.OFFICER]

        start_time = timezone.now()
        end_time = start_time + datetime.timedelta(hours=2)
        event = self.create_event(start_time, end_time)
        for restriction in restrictions:
            event.restriction = restriction
            event.save()
            if restriction == Event.PUBLIC:
                self.assert_can_sign_up(event, self.user)
            else:
                self.assert_cannot_sign_up(event, self.user)

        # Make this person a candidate, so the person should be able to sign up
        # for public and candidate events
        Candidate(user=self.user, term=self.term).save()
        for restriction in restrictions:
            event.restriction = restriction
            event.save()
            if (restriction == Event.PUBLIC or restriction == Event.CANDIDATE):
                self.assert_can_sign_up(event, self.user)
            else:
                self.assert_cannot_sign_up(event, self.user)

        # Make this person an officer, so the person should be able to sign up
        # for all events except open events (which don't allow signups)
        Officer(user=self.user, position=self.committee, term=self.term).save()
        for restriction in restrictions:
            event.restriction = restriction
            event.save()
            if restriction == Event.OPEN:
                self.assert_cannot_sign_up(event, self.user)
            else:
                self.assert_can_sign_up(event, self.user)

        # TODO(sjdemartini): add tests for members once UserProfile.is_member
        # is not purely LDAP-dependent

    def test_list_date(self):
        start_time = datetime.datetime(2015, 3, 14, 9, 26, 53, 59)
        start_time = timezone.make_aware(start_time,
                                         timezone.get_current_timezone())
        end_time = start_time + datetime.timedelta(hours=2)
        event = self.create_event(start_time, end_time,
                                  name='My Pi Day Event')
        self.assertEqual(event.list_date(), 'Sat, Mar 14')

        end_time = start_time + datetime.timedelta(days=1)
        event.end_datetime = end_time
        event.save()
        self.assertEqual(event.list_date(), 'Sat, Mar 14 - Sun, Mar 15')

        end_time = start_time + datetime.timedelta(days=3)
        event.end_datetime = end_time
        event.save()
        self.assertEqual(event.list_date(), 'Sat, Mar 14 - Tue, Mar 17')

    def test_list_time(self):
        start_time = datetime.datetime(2015, 3, 14, 9, 26, 53, 59)
        start_time = timezone.make_aware(start_time,
                                         timezone.get_current_timezone())
        end_time = start_time + datetime.timedelta(hours=2, minutes=6)
        event = self.create_event(start_time, end_time,
                                  name='My Pi Day Event')
        self.assertEqual(event.list_time(), '9:26 AM - 11:32 AM')

        end_time = start_time + datetime.timedelta(hours=11, minutes=2)
        event.end_datetime = end_time
        event.save()
        self.assertEqual(event.list_time(), '9:26 AM - 8:28 PM')

        end_time = start_time + datetime.timedelta(days=1, hours=11, minutes=2)
        event.end_datetime = end_time
        event.save()
        self.assertEqual(event.list_time(), '(3/14) 9:26 AM - (3/15) 8:28 PM')

        start_time = start_time.replace(hour=15, minute=14)
        end_time = start_time + datetime.timedelta(days=3, hours=5, minutes=29)
        event.start_datetime = start_time
        event.end_datetime = end_time
        event.save()
        self.assertEqual(event.list_time(), '(3/14) 3:14 PM - (3/17) 8:43 PM')

        event.end_datetime = event.start_datetime
        event.save()
        self.assertEqual(event.list_time(), 'TBA')

    def test_view_datetime(self):
        start_time = datetime.datetime(2015, 3, 14, 9, 26, 53, 59)
        start_time = timezone.make_aware(start_time,
                                         timezone.get_current_timezone())
        end_time = start_time + datetime.timedelta(hours=2, minutes=4)
        event = self.create_event(start_time, end_time,
                                  name='My Pi Day Event')
        self.assertEqual(event.view_datetime(),
                         'Sat, Mar 14 9:26 AM to 11:30 AM')

        end_time = start_time + datetime.timedelta(hours=11, minutes=2)
        event.end_datetime = end_time
        event.save()
        self.assertEqual(event.view_datetime(),
                         'Sat, Mar 14 9:26 AM to 8:28 PM')

        end_time = start_time + datetime.timedelta(days=1, hours=11, minutes=2)
        event.end_datetime = end_time
        event.save()
        self.assertEqual(event.view_datetime(),
                         'Sat, Mar 14 9:26 AM to Sun, Mar 15 8:28 PM')

        start_time = start_time.replace(hour=15, minute=14)
        end_time = start_time + datetime.timedelta(days=3, hours=5, minutes=29)
        event.start_datetime = start_time
        event.end_datetime = end_time
        event.save()
        self.assertEqual(event.view_datetime(),
                         'Sat, Mar 14 3:14 PM to Tue, Mar 17 8:43 PM')

        event.end_datetime = event.start_datetime
        event.save()
        self.assertEqual(event.view_datetime(), 'Sat, Mar 14 Time TBA')

    def test_unicode(self):
        start_time = timezone.now()
        end_time = start_time + datetime.timedelta(hours=2)
        event = self.create_event(start_time, end_time)
        signup = EventSignUp(name='Edward', event=event, num_guests=0)
        signup.save()
        expected_str = u'{name} has signed up for {event_name}'.format(
            name=signup.name, event_name=event.name)
        self.assertEqual(expected_str, unicode(signup))

        signup.person = self.user
        signup.save()
        expected_str = u'{name} has signed up for {event_name}'.format(
            name=self.user.get_full_name(), event_name=event.name)
        self.assertEqual(expected_str, unicode(signup))

        signup.num_guests = 1
        signup.save()
        expected_str = u'{name} (+1) has signed up for {event_name}'.format(
            name=self.user.get_full_name(), event_name=event.name)
        self.assertEqual(expected_str, unicode(signup))

        signup.num_guests = 2
        signup.save()
        expected_str = u'{name} (+2) has signed up for {event_name}'.format(
            name=self.user.get_full_name(), event_name=event.name)
        self.assertEqual(expected_str, unicode(signup))

        signup.unsignup = True
        signup.save()
        expected_str = u'{name} (+2) has unsigned up for {event_name}'.format(
            name=self.user.get_full_name(), event_name=event.name)
        self.assertEqual(expected_str, unicode(signup))


class EventFormsTest(EventTesting):
    def setUp(self):
        # Call superclass setUp first:
        EventTesting.setUp(self)

        start_datetime = timezone.now()
        start_datetime = start_datetime.replace(
            month=3, day=14, year=2015, hour=9, minute=26)
        end_datetime = start_datetime + datetime.timedelta(hours=2)
        self.event = self.create_event(start_datetime, end_datetime)

        # Create string formats for start and end times:
        # Note that we separate date and time into separate strings to be used
        # as input to the SplitDateTimeWidget for the DateTimeField, since
        # the widget splits input into two separate form fields.
        self.start_date = '{:%Y-%m-%d}'.format(self.event.start_datetime)
        self.start_time = '{:%I:%M%p}'.format(self.event.start_datetime)
        self.end_date = '{:%Y-%m-%d}'.format(self.event.end_datetime)
        self.end_time = '{:%I:%M%p}'.format(self.event.end_datetime)

    def create_basic_event_form(self, extra_fields=None):
        """Returns an event form with some of the common fields filled out.

        The extra_fields kwarg is used to pass a dictionary of additional
        fields to include when creating the form.  Note that without specifying
        some additional fields, the form returned is not a valid form, as event
        start and end times are required fields.
        """
        fields = {'name': self.event.name,
                  'event_type': self.event.event_type.pk,
                  'term': self.event.term.pk,
                  'contact': self.user.pk,
                  'committee': self.event.committee.pk,
                  'restriction': Event.OFFICER,
                  'location': self.event.location,
                  'requirements_credit': self.event.requirements_credit,
                  'max_guests_per_person': self.event.max_guests_per_person,
                  'signup_limit': self.event.signup_limit}
        if extra_fields:
            fields.update(extra_fields)
        return EventForm(fields)

    def test_clean(self):
        form = EventForm()
        # Blank form should be invalid:
        self.assertFalse(form.is_valid())

        # Create a form with all fields logically/properly filled out:
        form = self.create_basic_event_form(
            {'start_datetime_0': self.start_date,
             'start_datetime_1': self.start_time,
             'end_datetime_0': self.end_date,
             'end_datetime_1': self.end_time})
        self.assertTrue(form.is_valid())

        # Create an invalid form with invalid input for start and/or end time:
        start_error = ['Your start time is not in the proper format.']
        end_error = ['Your end time is not in the proper format.']
        end_before_start = ['Your event is scheduled to end before it starts.']
        # Missing start and end times:
        form = self.create_basic_event_form()
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.get('start_datetime', None),
                         start_error)
        self.assertEqual(form.errors.get('end_datetime', None),
                         end_error)

        # Missing start time:
        form = self.create_basic_event_form(
            {'end_datetime_0': self.end_date,
             'end_datetime_1': self.end_time})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.get('start_datetime', None),
                         start_error)
        self.assertIsNone(form.errors.get('end_datetime', None))

        # Invalid (non-datetime) end time:
        # (Note that the same validation error will occur if end_datetime not
        # specified.)
        form = self.create_basic_event_form(
            {'start_datetime_0': self.start_date,
             'start_datetime_1': self.start_time,
             'end_datetime_0': 'not a date',
             'end_datetime_1': 'not a time'})
        self.assertFalse(form.is_valid())
        self.assertIsNone(form.errors.get('start_datetime', None))
        self.assertEqual(form.errors.get('end_datetime', None),
                         end_error)

        # Create a form with event end time before start time:
        form = self.create_basic_event_form(
            {'start_datetime_0': self.end_date,
             'start_datetime_1': self.end_time,
             'end_datetime_0': self.start_date,
             'end_datetime_1': self.start_time})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.get('start_datetime', None),
                         end_before_start)
        self.assertEqual(form.errors.get('end_datetime', None),
                         end_before_start)

    def test_autocreate_project_report(self):
        """ Ensures that when an EventForm is saved, a project report
        corresponding to that event is created, depending on the needs_pr
        field.
        """
        # Create the fields for an Event, based on the event created in setUp,
        # simply with a different event name
        event_name_no_pr = 'My Event Without a PR'
        event_name_pr = 'My Event With a PR'
        fields = {'name': event_name_no_pr,
                  'event_type': self.event.event_type.pk,
                  'term': self.event.term.pk,
                  'contact': self.user.pk,
                  'committee': self.event.committee.pk,
                  'restriction': Event.OFFICER,
                  'location': self.event.location,
                  'requirements_credit': self.event.requirements_credit,
                  'max_guests_per_person': self.event.max_guests_per_person,
                  'signup_limit': self.event.signup_limit,
                  'start_datetime_0': self.start_date,
                  'start_datetime_1': self.start_time,
                  'end_datetime_0': self.end_date,
                  'end_datetime_1': self.end_time,
                  'needs_pr': False}

        # Ensure that saving the EventForm creates the event and that no
        # project report is created:
        EventForm(fields).save()
        event = get_object_or_none(Event, name=event_name_no_pr)
        self.assertIsNotNone(event)
        self.assertIsNone(event.project_report)
        self.assertFalse(ProjectReport.objects.all().exists())

        # Create event with form, requiring project report, and ensure PR
        # is created:
        fields.update({'name': event_name_pr,
                       'needs_pr': True})
        EventForm(fields).save()
        event = get_object_or_none(Event, name=event_name_pr)
        self.assertIsNotNone(event)
        self.assertTrue(ProjectReport.objects.all().exists())
        project_report = ProjectReport.objects.all()[0]

        # Check the properties of both the event and project report to ensure
        # that they were saved and match our form
        self.assertEqual(event.name, event_name_pr)
        self.assertEqual(project_report.title, event_name_pr)

        self.assertEqual(event.start_datetime.date(),
                         self.event.start_datetime.date())
        self.assertEqual(project_report.date,
                         self.event.start_datetime.date())

        self.assertEqual(event.contact, self.user)
        self.assertEqual(project_report.author, self.user)

        self.assertEqual(event.term, self.event.term)
        self.assertEqual(project_report.term, self.event.term)

        self.assertEqual(project_report, event.project_report)
