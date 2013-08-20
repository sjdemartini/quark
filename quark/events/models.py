from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils import timezone

from quark.base.models import Term
from quark.base_tbp.models import OfficerPosition
from quark.project_reports.models import ProjectReport


class EventTypeManager(models.Manager):
    def get_by_natural_key(self, name):
        try:
            return self.get(name=name)
        except EventType.DoesNotExist:
            return None


class EventType(models.Model):
    name = models.CharField(max_length=60, unique=True)

    objects = EventTypeManager()

    def __unicode__(self):
        return self.name

    def natural_key(self):
        return (self.name,)


class EventManager(models.Manager):
    def get_upcoming(self, current_term_only=True):
        """Return events that haven't been cancelled and haven't yet ended.

        If current_term_only is True, the method returns only upcoming events
        in the current term. Otherwise, the method returns upcoming events from
        all terms.
        """
        self = self.filter(cancelled=False, end_datetime__gt=timezone.now())
        if current_term_only:
            self = self.filter(term=Term.objects.get_current_term())
        return self


class Event(models.Model):
    name = models.CharField(max_length=80)
    event_type = models.ForeignKey(EventType)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    term = models.ForeignKey(Term)
    tagline = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=80)
    contact = models.ForeignKey(settings.AUTH_USER_MODEL)
    committee = models.ForeignKey(OfficerPosition)
    signup_limit = models.PositiveSmallIntegerField(
        default=0, help_text='Set as 0 to allow unlimited signups.')
    max_guests_per_person = models.PositiveSmallIntegerField(
        default=0,
        help_text='Maximum number of guests each person is allowed to bring.')
    needs_drivers = models.BooleanField(default=False)
    cancelled = models.BooleanField(default=False)

    # Some events can be worth more than 1 credit for candidates:
    requirements_credit = models.IntegerField(
        default=1,
        help_text='Large events can be worth more than 1 candidate '
                  'requirement credit.',
        choices=((0, 0), (1, 1), (2, 2), (3, 3)))

    project_report = models.ForeignKey(ProjectReport, null=True, blank=True,
                                       related_name='event', default=None)

    # TODO(sjdemartini): implement restrictions (who can see or sign up for
    # the event). One option is to create a class to handle restrictions.
    # Another option is as follows, if a UserType model (or similar) is
    # created:
    #restriction = models.ManyToManyField(
    #    UserType, help_text='Controls who can view/attend the event')

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = EventManager()

    class Meta(object):
        ordering = ('start_datetime',)
        permissions = (
            ('contact_participants', 'Can send email to those signed up'),
        )
        verbose_name = 'event'
        verbose_name_plural = 'events'

    def __unicode__(self):
        return '{} - {}'.format(self.name, unicode(self.term))

    # TODO(sjdemartini): implement get_absolute_url(self) for returning the
    # URL of an event object

    def is_upcoming(self):
        """Return True if the event is not canceled and has not yet ended."""
        return (not self.cancelled) and (self.end_datetime > timezone.now())

    def is_multiday(self):
        """Return True if the event starts on a different date than it ends.
        """
        return self.start_datetime.date() != self.end_datetime.date()

    def get_num_guests(self):
        """Return the number of guests signed-up users are bringing along.

        This number does not include the signed-up users, themselves; only
        their guests are counted here.
        """
        return (self.eventsignup_set.filter(unsignup=False).aggregate(
                Sum('num_guests'))['num_guests__sum'] or 0)

    def get_num_rsvps(self, include_guests=True):
        """Return the expected number of attendees based on signups.

        This value includes the total number of signed up users. If
        include_guests is True (as default), this count also includes the
        number of guests for each signup.
        """
        count = self.eventsignup_set.filter(unsignup=False).count()
        if include_guests:
            count += self.get_num_guests()
        return count

    def list_date(self):
        """Return a succinct string representation of the event date.

        An example is 'Sat, Nov 3'. For a multiday event, an example is
        'Mon, Mar 5 - Tue, Mar 6'.
        """
        date = Event.__get_abbrev_date_string(self.start_datetime)
        if self.is_multiday():
            date = '{} - {}'.format(
                date, Event.__get_abbrev_date_string(self.end_datetime))
        return date

    def list_time(self):
        """Return a succinct string representation of the event time.

        An example is '5:30 PM - 7:00 PM'. For a multiday event, the dates are
        included, as well. For instance, '(6/13) 11:15 PM - (6/14) 5:00 AM'.
        """
        start_time = Event.__get_time_string(self.start_datetime)
        end_time = Event.__get_time_string(self.end_datetime)
        if self.is_multiday():
            start_date = '({}/{})'.format(
                self.start_datetime.strftime('%m').lstrip('0'),
                self.start_datetime.strftime('%d').lstrip('0'))
            end_date = '({}/{})'.format(
                self.end_datetime.strftime('%m').lstrip('0'),
                self.end_datetime.strftime('%d').lstrip('0'))
            return '{} {} - {} {}'.format(
                start_date, start_time, end_date, end_time)
        elif start_time == end_time:
            return 'TBA'
        else:
            return '{} - {}'.format(start_time, end_time)

    def view_datetime(self):
        """Return a succinct string representation of the event date and time.

        An example is 'Sat, Nov 3 5:15 PM to 6:45 PM'. For a multiday event,
        an example is 'Mon, Mar 5 11:00 AM to Tue, Mar 6 11:00 AM'.
        """
        start_time = Event.__get_time_string(self.start_datetime)
        start_date = Event.__get_abbrev_date_string(self.start_datetime)
        end_string = Event.__get_time_string(self.end_datetime)
        if self.is_multiday():
            end_string = '{} {}'.format(
                Event.__get_abbrev_date_string(self.end_datetime), end_string)
        elif start_time == end_string:
            return '{} Time TBA'.format(start_date)
        return '{} {} to {}'.format(start_date, start_time, end_string)

    # TODO(sjdemartini): re-implement Google Calendar utilities

    # TODO(sjdemartini): re-implement attendence_submitted() function

    # TODO(sjdemartini): re-implement sending email to VPs when event saved

    @staticmethod
    def __get_abbrev_date_string(datetime_object):
        """Return a 'weekday, month day#' abbreviated string representation of
        the datetime object.

        An example output could be 'Sat, Nov 3'.
        """
        return '{} {}'.format(datetime_object.strftime('%a, %b'),
                              datetime_object.strftime("%d").lstrip('0'))

    @staticmethod
    def __get_time_string(datetime_object):
        """Return the current time in 12-hour AM/PM format.

        An example output could be '10:42 PM'.
        """
        return datetime_object.strftime("%I:%M %p").lstrip('0')


class EventSignUp(models.Model):
    event = models.ForeignKey(Event)
    person = models.ForeignKey(settings.AUTH_USER_MODEL, null=True)
    name = models.CharField(max_length=255)  # Person's name used for signup
    num_guests = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='number of guests you are bringing')
    driving = models.PositiveSmallIntegerField(
        default=0,
        verbose_name=('how many people fit in your car, including yourself '
                      '(0 if not driving)'))
    comments = models.TextField(
        blank=True, verbose_name='comments (optional)')

    # Necessary for anonymous signups (when person is null):
    email = models.EmailField(
        blank=True, verbose_name='email address',
        help_text='Your email address will act as your password to unsign up.')

    timestamp = models.DateTimeField(auto_now=True)

    unsignup = models.BooleanField(default=False)

    class Meta(object):
        ordering = ('timestamp',)
        permissions = (
            ('view_signups', 'Can view who has signed up for events'),
            ('view_comments', 'Can view sign-up comments'),
        )

    def __unicode__(self):
        action = 'unsigned' if self.unsignup else 'signed'
        if self.person is None:
            name = self.name
        else:
            name = self.person.get_common_name()
        guest_string = (
            ' (+{})'.format(self.num_guests) if self.num_guests > 0 else '')
        return '{person}{guests} has {action} up for {event_name}'.format(
            person=name,
            guests=guest_string,
            action=action,
            event_name=self.event.name)


class EventAttendance(models.Model):
    event = models.ForeignKey(Event)
    person = models.ForeignKey(settings.AUTH_USER_MODEL)

    # TODO(sjdemartini): Deal with the pre-noiro attendance importing? Note
    # that noiro added a separate field here to handle pre-noiro attendance
    # imports, as well as ImportedAttendance objects

    def __unicode__(self):
        return '{} attended {}'.format(self.person.get_common_name(),
                                       self.event.name)

    class Meta(object):
        unique_together = ('event', 'person')
