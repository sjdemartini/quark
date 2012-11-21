import datetime

from django.db import models
from django.utils import timezone


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
            start = timezone.make_aware(
                datetime.datetime(
                    year - 1, Season.START_MONTH, Season.START_DAY),
                SeasonManager.TIMEZONE)
            end = timezone.make_aware(
                datetime.datetime(
                    year, Season.END_MONTH, Season.END_DAY),
                SeasonManager.TIMEZONE)
            return Season(year=end.year, start_date=start, end_date=end)

    def generate_start_end_dates(self, year):
        """Returns the start and end dates given the end date's year"""
        start = timezone.make_aware(
            datetime.datetime(
                year - 1, Season.START_MONTH, Season.START_DAY),
            SeasonManager.TIMEZONE)
        end = timezone.make_aware(
            datetime.datetime(
                year, Season.END_MONTH, Season.END_DAY),
            SeasonManager.TIMEZONE)
        return start, end


class Season(models.Model):
    """The Season Model contains information about the given Season."""
    # The first PiE Season was in 2009
    FIRST_YEAR = 2009

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
        return "PiE Season %d" % self.year

    def __unicode__(self):
        season = self.verbose_name()
        if self.is_current():
            season += ' (Current)'
        return season

    @property
    def season_number(self):
        """The Season number, 2009 is Season 1"""
        if self.year - Season.FIRST_YEAR + 1 < 1:
            raise ValueError('Season must be %d or greater' % Season.FIRST_YEAR)
        return self.year - Season.FIRST_YEAR + 1
