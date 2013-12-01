from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Sum
from django.db.models.query import QuerySet
from django.template import defaultfilters
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


class EventQuerySetMixin(object):
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

    def get_user_viewable(self, user):
        """Return events that the given user can view.

        Viewability is based on the "restriction" level for the events.
        """
        user_level = Event.get_user_restriction_level(user)

        # Initialize visible_levels to those that are visible to everyone
        visible_levels = Event.VISIBLE_TO_EVERYONE
        if user_level >= Event.MEMBER:
            visible_levels.append(Event.MEMBER)
        if user_level >= Event.OFFICER:
            visible_levels.append(Event.OFFICER)
        return self.filter(restriction__in=visible_levels)


class EventQuerySet(QuerySet, EventQuerySetMixin):
    """Used in order to allow chaining of manager methods."""
    pass


class EventManager(models.Manager, EventQuerySetMixin):
    """Manager that allows for chaining of methods of its mixin.

    Based on https://djangosnippets.org/snippets/2114/
    """
    def get_query_set(self):
        return EventQuerySet(self.model, using=self._db)


class Event(models.Model):
    # Restriction constants
    PUBLIC = 0
    CANDIDATE = 1
    MEMBER = 2
    OFFICER = 3
    OPEN = 4

    RESTRICTION_CHOICES = (
        (PUBLIC, 'Public'),
        (CANDIDATE, 'Candidate'),
        (MEMBER, 'Member'),
        (OFFICER, 'Officer'),
        (OPEN, 'Open (No Signups)')
    )

    VISIBLE_TO_EVERYONE = [OPEN, PUBLIC, CANDIDATE]

    name = models.CharField(max_length=80, verbose_name='event name')
    event_type = models.ForeignKey(EventType)

    restriction = models.PositiveSmallIntegerField(
        choices=RESTRICTION_CHOICES,
        default=CANDIDATE,
        db_index=True,
        verbose_name='minimum restriction',
        help_text=(
            'Who can sign up for this? Each restriction level allows users in '
            'that category, as well as users with more permissions (e.g., '
            'setting the restriction as "Candidate" allows candidates, '
            'members, and officers).'))

    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    term = models.ForeignKey(Term)
    tagline = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=80)
    contact = models.ForeignKey(settings.AUTH_USER_MODEL)
    committee = models.ForeignKey(OfficerPosition, null=True)

    signup_limit = models.PositiveSmallIntegerField(
        default=0,
        help_text='Set as 0 to allow unlimited signups.')
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
        return u'{} - {}'.format(self.name, unicode(self.term))

    def get_absolute_url(self):
        return reverse('events:detail', args=(self.pk,))

    def is_upcoming(self):
        """Return True if the event is not canceled and has not yet ended."""
        return (not self.cancelled) and (self.end_datetime > timezone.now())

    def is_multiday(self):
        """Return True if the event starts on a different date than it ends.

        Ensures that the multiday check uses the current timezone.
        """
        start_date = timezone.localtime(self.start_datetime).date()
        end_date = timezone.localtime(self.end_datetime).date()
        return start_date != end_date

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

    def can_user_sign_up(self, user):
        """Return true if the given user is allowed to sign up for this event.

        This method is based on the "restriction" level for the event.
        """
        return Event.get_user_restriction_level(user) >= self.restriction

    def can_user_view(self, user):
        """Return true if the given user is allowed to view this event.

        This method is based on the "restriction" level for the event.
        Note that CANDIDATE-restricted events are publicly visible (though
        still restricting signups).
        """
        if self.restriction in Event.VISIBLE_TO_EVERYONE:
            return True
        return Event.get_user_restriction_level(user) >= self.restriction

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
            start_datetime = timezone.localtime(self.start_datetime)
            start_date = defaultfilters.date(start_datetime, 'n/j')
            end_datetime = timezone.localtime(self.end_datetime)
            end_date = defaultfilters.date(end_datetime, 'n/j')
            return '({}) {} - ({}) {}'.format(
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

        Ensures that the time is displayed in the current timezone.

        An example output could be 'Sat, Nov 3'.
        """
        datetime_object = timezone.localtime(datetime_object)
        return defaultfilters.date(datetime_object, 'D, M j')

    @staticmethod
    def __get_time_string(datetime_object):
        """Return the current time in 12-hour AM/PM format.

        Ensures that the time is displayed in the current timezone.

        An example output could be '10:42 PM'.
        """
        datetime_object = timezone.localtime(datetime_object)
        return defaultfilters.date(datetime_object, 'g:i A')

    @staticmethod
    def get_user_restriction_level(user):
        """Return the maximum event restriction level this user can access."""
        if user.is_authenticated():
            if user.userprofile.is_officer():
                return Event.OFFICER
            elif user.userprofile.is_member():
                return Event.MEMBER
            elif user.userprofile.is_candidate():
                return Event.CANDIDATE
        return Event.PUBLIC


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
            name = self.person.get_full_name()
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
        return '{} attended {}'.format(self.person.get_full_name(),
                                       self.event.name)

    class Meta(object):
        unique_together = ('event', 'person')
