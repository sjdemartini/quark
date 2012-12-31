import datetime

from django.test import TestCase
from django.utils import timezone

from quark.auth.models import User
from quark.base.models import OfficerPosition
from quark.base.models import Term
from quark.events.models import Event
from quark.events.models import EventType


class EventsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='officer',
            email='it@tbp.berkeley.edu',
            password='testofficerpw',
            first_name='Off',
            last_name='Icer')

        self.committee = OfficerPosition(
            position_type=OfficerPosition.TBP_OFFICER,
            short_name='IT_test',
            long_name='Information Technology (test)',
            rank=2,
            mailing_list='IT')
        self.committee.save()

        self.term = Term(term=Term.SPRING, year=2012, current=True)
        self.term.save()

        self.event_type, _ = EventType.objects.get_or_create(
            name='Test Event Type')

    def test_eventtype_get_by_natural_key(self):
        event_type_name = 'New Test Event Type'
        EventType(name=event_type_name).save()
        event_type = EventType.objects.get_by_natural_key(event_type_name)
        self.assertEqual(event_type.name, event_type_name)

    def test_eventtype_get_by_natural_key_does_not_exist(self):
        event_type = EventType.objects.get_by_natural_key(
            'New Test Event Type')
        self.assertIsNone(event_type)

    def test_is_upcoming(self):
        # Create an event that hasn't started yet:
        start_time = timezone.now() + datetime.timedelta(hours=2)
        end_time = start_time + datetime.timedelta(hours=3)
        event = Event(name='My Test Event',
                      event_type=self.event_type,
                      term=self.term,
                      start_datetime=start_time,
                      end_datetime=end_time,
                      location='A test location',
                      contact=self.user)
        event.save()
        self.assertTrue(event.is_upcoming())
        event.cancelled = True
        event.save()
        self.assertFalse(event.is_upcoming())

        # Create an event that has already started but hasn't ended yet:
        start_time = timezone.now() - datetime.timedelta(hours=2)
        end_time = timezone.now() + datetime.timedelta(hours=3)
        event = Event(name='My Ongoing Event',
                      event_type=self.event_type,
                      term=self.term,
                      start_datetime=start_time,
                      end_datetime=end_time,
                      location='Another test location',
                      contact=self.user)
        event.save()
        self.assertTrue(event.is_upcoming())
        event.cancelled = True
        event.save()
        self.assertFalse(event.is_upcoming())

        # Create an event that has already ended:
        start_time = timezone.now() - datetime.timedelta(days=2)
        end_time = start_time + datetime.timedelta(hours=3)
        event = Event(name='My Old Event',
                      event_type=self.event_type,
                      term=self.term,
                      start_datetime=start_time,
                      end_datetime=end_time,
                      location='Yet another test location',
                      contact=self.user)
        event.save()
        self.assertFalse(event.is_upcoming())
        event.cancelled = True
        event.save()
        self.assertFalse(event.is_upcoming())

    def test_is_multiday(self):
        start_time = timezone.now()
        end_time = start_time + datetime.timedelta(days=1)
        event = Event(name='My Multiday Event',
                      event_type=self.event_type,
                      term=self.term,
                      start_datetime=start_time,
                      end_datetime=end_time,
                      location='A test location',
                      contact=self.user)
        event.save()
        self.assertTrue(event.is_multiday())

        end_time = start_time + datetime.timedelta(weeks=1)
        event = Event(name='My Weeklong Event',
                      event_type=self.event_type,
                      term=self.term,
                      start_datetime=start_time,
                      end_datetime=end_time,
                      location='A test location',
                      contact=self.user)
        event.save()
        self.assertTrue(event.is_multiday())

        # Ensure that the start hour is not so late in the day that the end
        # time goes into the following day:
        start_time = start_time.replace(hour=3, minute=14)
        end_time = start_time + datetime.timedelta(hours=15)
        event = Event(name='My Non-multiday Event',
                      event_type=self.event_type,
                      term=self.term,
                      start_datetime=start_time,
                      end_datetime=end_time,
                      location='A test location',
                      contact=self.user)
        event.save()
        self.assertFalse(event.is_multiday())

    def test_list_date(self):
        start_time = timezone.now()
        start_time = start_time.replace(month=3, day=14, year=2015, hour=9,
                                        minute=26)
        end_time = start_time + datetime.timedelta(hours=2)
        event = Event(name='My Pi Day Event',
                      event_type=self.event_type,
                      term=self.term,
                      start_datetime=start_time,
                      end_datetime=end_time,
                      location='A test location',
                      contact=self.user)
        event.save()
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
        start_time = timezone.now()
        start_time = start_time.replace(month=3, day=14, year=2015, hour=9,
                                        minute=26)
        end_time = start_time + datetime.timedelta(hours=2, minutes=6)
        event = Event(name='My Pi Day Event',
                      event_type=self.event_type,
                      term=self.term,
                      start_datetime=start_time,
                      end_datetime=end_time,
                      location='A test location',
                      contact=self.user)
        event.save()
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
        start_time = timezone.now()
        start_time = start_time.replace(month=3, day=14, year=2015, hour=9,
                                        minute=26)
        end_time = start_time + datetime.timedelta(hours=2, minutes=4)
        event = Event(name='My Pi Day Event',
                      event_type=self.event_type,
                      term=self.term,
                      start_datetime=start_time,
                      end_datetime=end_time,
                      location='A test location',
                      contact=self.user)
        event.save()
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

    def test_get_committee(self):
        start_time = timezone.now() + datetime.timedelta(hours=2)
        end_time = start_time + datetime.timedelta(hours=3)
        event = Event(name='My Test Event',
                      event_type=self.event_type,
                      term=self.term,
                      start_datetime=start_time,
                      end_datetime=end_time,
                      location='A test location',
                      contact=self.user)
        event.save()
        self.assertEqual(event.get_committee(), None)

        event.committee = self.committee
        event.save()
        self.assertEqual(event.get_committee(), self.committee)
