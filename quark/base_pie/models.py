import datetime

from django.conf import settings
from django.db import models
from django.utils import timezone
from django_localflavor_us.models import USStateField

from quark.base.models import IDCodeMixin
from quark.base.models import Term


class SeasonManager(models.Manager):
    TIMEZONE = timezone.get_current_timezone()

    def get_current_season(self, date=None):
        """Returns either the current season or the one for the given date."""
        date = date or timezone.now().date()
        try:
            return Season.objects.get(start_date__lte=date, end_date__gte=date)
        except Season.DoesNotExist:
            # If there isn't a season that is current then we create one.
            # Seasons are known by the year that the Final Competition occurs
            # ie Final Competition on May 3, 2012 is part of the 2012 Season.
            # Thus if we want to create a new Season it is based on the year.
            # If the given date is after the season ended
            # but before the new year
            # then we will increment the year to properly label the season.
            # Example: Given date is 8/17/2012 then we are in the 2013 Season.
            # If the given date is 2/3/2012 then that is in the 2012 Season.
            if date.month > Season.END_MONTH:
                year = date.year + 1
            else:
                year = date.year

            start, end = Season.generate_start_end_dates(year)
            new_season = Season(year=end.year, start_date=start, end_date=end)
            new_season.save()
            return new_season


class Season(models.Model):
    """The Season Model contains information about the given Season."""
    # The first PiE Season was in 2009
    FIRST_YEAR = 2009
    BAD_YEAR_MESSAGE = 'Season must be %d or greater' % FIRST_YEAR

    # The PiE Season starts after the previous one ends,
    # by using the beginning of the month this allows for easier implementation.
    # Currently set to June 1st.
    START_DAY = 1
    START_MONTH = 6

    # The PiE Season ends after Final Competition,
    # want to include buffer for any events that are still part of Season.
    # Currently set to May 31st.
    END_DAY = 31
    END_MONTH = 5

    year = models.PositiveIntegerField(primary_key=True)
    start_date = models.DateField()
    end_date = models.DateField()

    objects = SeasonManager()

    def __unicode__(self):
        season = self.verbose_name()
        if self.is_current():
            season += ' (Current)'
        return season

    def save(self, *args, **kwargs):
        if not Season.is_valid_year(self.year):
            raise ValueError(Season.BAD_YEAR_MESSAGE)
        super(Season, self).save(*args, **kwargs)

    @staticmethod
    def is_valid_year(year):
        try:
            return int(year) - Season.FIRST_YEAR >= 0
        except (TypeError, ValueError):
            return False

    def is_current(self):
        """Returns a boolean of whether the given season is the current one."""
        today = timezone.now().date()
        # The Season is current if today is part of the Season
        # For today to be part of the season it is either in the Spring
        # portion and before the end of the Season
        # or in the Fall and after the beginning of the Season.
        # By making the Season begin on 6/1 and ending on 5/31 we can
        # just check that the year to find which part of the Season and
        # the month to make sure it is within the bounds.
        return ((today.year == self.year and today.month < Season.START_MONTH)
                or (
                today.year + 1 == self.year and today.month > Season.END_MONTH))

    def verbose_name(self):
        return 'PiE Season %d' % self.year

    @property
    def season_number(self):
        """The 2009 Season is the first season"""
        if not Season.is_valid_year(self.year):
            raise ValueError(Season.BAD_YEAR_MESSAGE)
        return self.year - Season.FIRST_YEAR + 1

    def get_corresponding_term(self):
        """Returns the term corresponding to this PiE Season if one exists, or
        None otherwise.

        First, this method checks whether the current term maps to this PiE
        season and returns it if so. Otherwise, because a year 2013 Season
        encompasses Summer 2012 through Spring 2013, Season x will be set to
        Spring x. If Spring x does not exist, then the following terms will be
        examined to test if they exist instead, before returning None: Winter
        x, Fall (x-1), Summer (x-1).
        """

        # Check current term:
        current_term = Term.objects.get_current_term()
        if self == Season.get_pie_season_from_term(current_term):
            return current_term

        # Otherwise find term nearest to Spring that exists for this Season:
        terms = [Term.SPRING, Term.WINTER, Term.FALL, Term.SUMMER]
        year_offset_map = {
            Term.SPRING: 0,
            Term.WINTER: 0,
            Term.FALL: -1,
            Term.SUMMER: -1
        }
        # TODO(sjdemartini): Optimize finding the correct Term, rather than
        # cycling through try-except in a for-loop
        for term in terms:
            try:
                return Term.objects.get(year=self.year + year_offset_map[term],
                                        term=term)
            except Term.DoesNotExist:
                pass
        return None

    @staticmethod
    def get_pie_season_from_term(term):
        """Returns the PiE season corresponding to this term if one exists, or
        None otherwise."""
        if term.term in [Term.SUMMER, Term.FALL]:
            month = Season.START_MONTH
        else:
            month = Season.END_MONTH
        return Season.objects.get_current_season(
            datetime.date(year=term.year, month=month, day=1))

    @staticmethod
    def generate_start_end_dates(year):
        """Returns the start and end dates as timezone aware datetime objects
        given the end date's year."""
        start = timezone.make_aware(
            datetime.datetime(
                year - 1, Season.START_MONTH, Season.START_DAY),
            SeasonManager.TIMEZONE)
        end = timezone.make_aware(
            datetime.datetime(
                year, Season.END_MONTH, Season.END_DAY),
            SeasonManager.TIMEZONE)
        return start, end


class School(models.Model):
    # School name
    name = models.CharField(max_length=200, unique=True)

    # The address of the school
    street_number = models.IntegerField()
    street = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = USStateField()
    zipcode = models.IntegerField()

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('name',)


class Team(models.Model):
    number = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=100)

    school = models.ForeignKey(School)
    season = models.ForeignKey(Season)

    active = models.BooleanField(default=True)
    car_required = models.BooleanField(default=False)
    extra_attention = models.BooleanField(default=False)

    created = models.DateField(auto_now_add=True)
    updated = models.DateField(auto_now=True)

    def __unicode__(self):
        if self.name:
            return '%s, Team %d (%s, %d Season)' % (
                self.name, self.number, self.school.name,
                self.season.season_number())
        else:
            return '%s Team %d (%d Season)' % (
                self.school.name, self.number,
                self.season.season_number())

    def friendly_name(self):
        return 'Team %d: %s' % (self.number, self.school)

    class Meta:
        unique_together = ('number', 'season')
        ordering = ('number',)


class Teacher(IDCodeMixin):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    team = models.ForeignKey(Team)

    created = models.DateField(auto_now_add=True)
    updated = models.DateField(auto_now=True)

    def __unicode__(self):
        return 'Teacher %s for %s' % (self.user, self.team.friendly_name())


class Mentor(IDCodeMixin):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    team = models.ForeignKey(Team)

    created = models.DateField(auto_now_add=True)
    updated = models.DateField(auto_now=True)

    def __unicode__(self):
        return 'Mentor %s for %s' % (self.user, self.team.friendly_name())


class Student(IDCodeMixin):
    FRESHMAN = 9
    SOPHOMORE = 10
    JUNIOR = 11
    SENIOR = 12
    SCHOOL_LEVELS = (
        (FRESHMAN, 'Freshman'),
        (SOPHOMORE, 'Sophomore'),
        (JUNIOR, 'Junior'),
        (SENIOR, 'Senior'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    team = models.ForeignKey(Team)

    # Leaders are allowed to edit the roster and assign editing power
    # to other members of a team.
    leader = models.BooleanField(default=False)

    year_in_school = models.PositiveSmallIntegerField(choices=SCHOOL_LEVELS)

    created = models.DateField(auto_now_add=True)
    updated = models.DateField(auto_now=True)

    def __unicode__(self):
        return 'Student %s for %s' % (self.user, self.team.friendly_name())
