from django.db import models
from django.utils import timezone

from quark.auth.models import User
from quark.base.models import OfficerPosition
from quark.base.models import Term


class EventTypeManager(models.Manager):
    def get_by_natural_key(self, name):
        try:
            return self.get(name=name)
        except EventType.DoesNotExist:
            return None


class EventType(models.Model):
    objects = EventTypeManager()

    name = models.CharField(max_length=60, unique=True)

    # TODO(sjdemartini): define colors mechanism to be used for event types'
    # color field. A viable option appears to be webcolors:
    # http://docs.b-list.org/webcolors/1.4/

    def __unicode__(self):
        return self.name

    def natural_key(self):
        return (self.name,)


class Event(models.Model):
    # TODO(sjdemartini): add PiE-specific considerations for event restrictions
    RESTRICTION_CHOICES = (
        (0, 'Public'),
        (1, 'Candidate'),
        (2, 'Member'),
        (3, 'Officer'),
        (4, 'Open (No Signups)'),
    )

    RESTRICTION_DICT = dict((v, k) for k, v in RESTRICTION_CHOICES)

    name = models.CharField(max_length=80)
    event_type = models.ForeignKey(EventType)
    restriction = models.PositiveSmallIntegerField(
        choices=RESTRICTION_CHOICES, default=RESTRICTION_DICT['Candidate'])
    term = models.ForeignKey(Term)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    tagline = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=80)
    contact = models.ForeignKey(User)
    committee = models.ForeignKey(OfficerPosition, null=True, blank=True)
    signup_limit = models.PositiveSmallIntegerField(default=0)
    needs_drivers = models.BooleanField(default=False)
    cancelled = models.BooleanField(default=False)

    # Some events can be worth more than 1 credit:
    requirements_credit = models.IntegerField(
        default=1,
        help_text='Large events can be worth more than 1 candidate '
                  'requirement credit.',
        choices=((0, 0), (1, 1), (2, 2), (3, 3)))

    # TODO(sjdemartini): add project reports field

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('start_datetime',)
        verbose_name = 'event'
        verbose_name_plural = 'events'

    def is_upcoming(self):
        return (not self.cancelled) and (
            self.end_datetime > timezone.now())

    def is_multiday(self):
        return self.start_datetime.date() != self.end_datetime.date()

    def list_date(self):
        """Returns a succinct string representation of the event date.

        An example is 'Sat, Nov 3'. For a multiday event, an example is
        'Mon, Mar 5 - Tue, Mar 6'.
        """
        date = Event.__get_abbrev_date_string(self.start_datetime)
        if self.is_multiday():
            date = '%s - %s' % (
                date, Event.__get_abbrev_date_string(self.end_datetime))
        return date

    def list_time(self):
        """Returns a succinct string representation of the event time.

        An example is '5:30 PM - 7:00 PM'. For a multiday event, the dates are
        included, as well. For instance, '(6/13) 11:15 PM - (6/14) 5:00 AM'.
        """
        start_time = Event.__get_time_string(self.start_datetime)
        end_time = Event.__get_time_string(self.end_datetime)
        if self.is_multiday():
            start_date = '(%s/%s)' % (
                self.start_datetime.strftime('%m').lstrip('0'),
                self.start_datetime.strftime('%d').lstrip('0'))
            end_date = '(%s/%s)' % (
                self.end_datetime.strftime('%m').lstrip('0'),
                self.end_datetime.strftime('%d').lstrip('0'))
            return '%s %s - %s %s' % (start_date, start_time, end_date,
                                      end_time)
        elif start_time == end_time:
            return 'TBA'
        else:
            return '%s - %s' % (start_time, end_time)

    def view_datetime(self):
        """Returns a succinct string representation of the event date and time.

        An example is 'Sat, Nov 3 5:15 PM to 6:45 PM'. For a multiday event,
        an example is 'Mon, Mar 5 11:00 AM to Tue, Mar 6 11:00 AM'.
        """
        start_time = Event.__get_time_string(self.start_datetime)
        start_date = Event.__get_abbrev_date_string(self.start_datetime)
        end_string = Event.__get_time_string(self.end_datetime)
        if self.is_multiday():
            end_string = '%s %s' % (
                Event.__get_abbrev_date_string(self.end_datetime), end_string)
        elif start_time == end_string:
            return '%s Time TBA' % start_date
        return '%s %s to %s' % (start_date, start_time, end_string)

    # TODO(sjdemartini): re-implement Google Calendar utilities

    # TODO(sjdemartini): re-implement attendence_submitted() function

    def get_committee(self):
        # TODO(sjdemartini): modify so that it checks if self.committee is
        # None, and if so, it returns the OfficerPosition of the user who
        # created the event (self.user) and returns that committee
        return self.committee

    def __unicode__(self):
        return u'%s - %s' % (self.name, unicode(self.term))

    # TODO(sjdemartini): re-implement sending email to VPs when event saved

    @staticmethod
    def __get_abbrev_date_string(datetime_object):
        """Returns a 'weekday, month day#' abbreviated string representation of
        the datetime object.

        An example output could be 'Sat, Nov 3'.
        """
        return '%s %s' % (datetime_object.strftime('%a, %b'),
                          datetime_object.strftime("%d").lstrip('0'))

    @staticmethod
    def __get_time_string(datetime_object):
        """Returns the current time in 12-hour AM/PM format.

        An example output could be '10:42 PM'.
        """
        return datetime_object.strftime("%I:%M %p").lstrip('0')
