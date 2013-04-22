import datetime
import mox

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from django.utils.timezone import make_aware

from quark.base.models import Term
from quark.base_pie.models import School
from quark.base_pie.models import Season
from quark.base_pie.models import Team
from quark.base_tbp.models import OfficerPosition


class SeasonManagerTest(TestCase):
    def assertSeasonEquals(self, season, year, start, end):
        self.assertEquals(season.year, year)
        self.assertEquals(season.start_date, start)
        self.assertEquals(season.end_date, end)

    def assertSeasonSaved(self, season):
        # Check if an object matching this Season exists in the database.
        # Django doesn't have a good way of actually checking this, so the best
        # we can do is verify that an object with all the same fields set to
        # the same values exists in the database.
        self.assertTrue(
            Season.objects.filter(pk=season.pk,
                                  year=season.year,
                                  start_date=season.start_date,
                                  end_date=season.end_date).exists())

    def assertSeasonNotSaved(self, season):
        # Reverse of the above.
        self.assertFalse(
            Season.objects.filter(pk=season.pk,
                                  year=season.year,
                                  start_date=season.start_date,
                                  end_date=season.end_date).exists())

    def setUp(self):
        self.mox = mox.Mox()
        self.tz = timezone.get_current_timezone()

    def tearDown(self):
        self.mox.UnsetStubs()

    def test_create_nonexisting_season(self):
        # Make sure a valid season is saved properly
        date = make_aware(datetime.datetime(2012, 02, 01), self.tz)
        season = Season.objects.get_current_season(date)
        self.assertSeasonSaved(season)

        start, end = Season.generate_start_end_dates(2012)
        season.year = 2012
        season.start_date = start
        season.end_date = end
        season.save()
        self.assertSeasonSaved(season)

    def test_no_create_bad_season(self):
        # Make sure a season with a bad date isn't saved
        date = make_aware(datetime.datetime(2005, 02, 01), self.tz)
        with self.assertRaises(ValueError):
            season = Season.objects.get_current_season(date)

        # No date information at all
        season = Season()
        with self.assertRaises(ValueError):
            season.save()

        # Year too early
        season.year = 2005
        with self.assertRaises(ValueError):
            season.save()

        # Make a valid season object...
        start, end = Season.generate_start_end_dates(2012)
        season = Season(year=2012, start_date=start, end_date=end)
        season.save()
        self.assertSeasonSaved(season)

        # ...then make sure modifying it to be invalid doesn't work
        season.year = 2005
        with self.assertRaises(ValueError):
            season.save()
        self.assertSeasonNotSaved(season)

    def test_season_does_not_already_exist_yearly_year(self):
        date = make_aware(datetime.datetime(2012, 02, 01), self.tz)
        season = Season.objects.get_current_season(date)
        start, end = Season.generate_start_end_dates(date.year)
        self.assertSeasonEquals(season, 2012, start, end)

    def test_season_does_not_already_exist_mid_year(self):
        date = make_aware(datetime.datetime(2011, 06, 01), self.tz)
        season = Season.objects.get_current_season(date)
        start, end = Season.generate_start_end_dates(date.year + 1)
        self.assertSeasonEquals(season, 2012, start, end)

    def test_season_does_not_already_exist_late_year(self):
        date = make_aware(datetime.datetime(2011, 11, 01), self.tz)
        season = Season.objects.get_current_season(date)
        start, end = Season.generate_start_end_dates(date.year + 1)
        self.assertSeasonEquals(season, 2012, start, end)

    def test_get_current_existing_season(self):
        date = make_aware(datetime.datetime(2011, 11, 11), self.tz)
        season = Season.objects.get_current_season(date)
        start, end = Season.generate_start_end_dates(date.year + 1)
        Season(year=date.year, start_date=start, end_date=end).save()
        self.assertSeasonEquals(season, 2012, start, end)
        self.assertFalse(season.is_current())

    def test_verbose_season_name(self):
        date = make_aware(datetime.datetime(2013, 11, 11), self.tz)
        season = Season.objects.get_current_season(date)
        self.assertEquals(season.verbose_name(), 'PiE Season 2014')

        date = make_aware(datetime.datetime(2012, 03, 02), self.tz)
        season = Season.objects.get_current_season(date)
        self.assertEquals(season.verbose_name(), 'PiE Season 2012')

    def test_season_number(self):
        start, end = Season.generate_start_end_dates(2012)
        season = Season(year=2012, start_date=start, end_date=end)
        self.assertEquals(season.season_number, 4)

        start, end = Season.generate_start_end_dates(2025)
        season = Season(year=2025, start_date=start, end_date=end)
        self.assertEquals(season.season_number, 17)

        start, end = Season.generate_start_end_dates(2005)
        season = Season(year=2012, start_date=start, end_date=end)
        season.year = 2005
        with self.assertRaises(ValueError):
            _ = season.season_number

    def test_get_current(self):
        # Will first test with no arguments to check that it gets the current
        # season in that case, then test for with a date passed.

        # Since get_current depends on timezone.now(), we will use mox.
        # StubOut timezone.now() so that we can test get_current regardless
        # of the date constantly changing. By stubbing out it treats
        # 2012, 01, 01 as the date for today and puts everything relative to it
        self.mox.StubOutWithMock(timezone, 'now')

        # Since timezone.now() is used in two places for getting the current
        # season, we need to return the same object all the time.
        timezone.now().MultipleTimes().AndReturn(
            datetime.datetime(2012, 01, 01))

        self.mox.ReplayAll()
        season = Season.objects.get_current_season()
        self.assertTrue(season.is_current())
        self.mox.VerifyAll()

    def test_is_current(self):
        # Similar to the above test but tests is_current()
        self.mox.StubOutWithMock(timezone, 'now')
        timezone.now().MultipleTimes().AndReturn(
            datetime.datetime(2012, 01, 01))

        self.mox.ReplayAll()
        date = make_aware(datetime.datetime(2012, 01, 01), self.tz)
        season = Season.objects.get_current_season(date)
        start, end = Season.generate_start_end_dates(2012)
        self.assertTrue(season.is_current())
        self.assertSeasonEquals(season, 2012, start, end)

        date = make_aware(datetime.datetime(2010, 9, 17), self.tz)
        season = Season.objects.get_current_season(date)
        start, end = Season.generate_start_end_dates(2011)
        self.assertFalse(season.is_current())
        self.assertSeasonEquals(season, 2011, start, end)
        self.mox.VerifyAll()

    def test_get_current_season_with_date(self):
        date = make_aware(datetime.datetime(2025, 3, 17), self.tz)
        season = Season.objects.get_current_season(date)
        self.assertEquals(season.year, date.year)

        date = make_aware(datetime.datetime(2009, 3, 17), self.tz)
        season = Season.objects.get_current_season(date)
        self.assertEquals(season.year, date.year)
        start, end = Season.generate_start_end_dates(date.year)
        Season(year=date.year, start_date=start, end_date=end).save()
        season = Season.objects.get_current_season(date)
        self.assertEquals(season.year, date.year)


class SeasonTest(TestCase):
    def setUp(self):
        self.term_sp12 = Term(term=Term.SPRING, year=2012)
        self.term_sp12.save()

        self.term_su12 = Term(term=Term.SUMMER, year=2012)
        self.term_su12.save()

        self.term_fa12 = Term(term=Term.FALL, year=2012)
        self.term_fa12.save()

        self.term_sp13 = Term(term=Term.SPRING, year=2013)
        self.term_sp13.save()

        self.term_su13 = Term(term=Term.SUMMER, year=2013)
        self.term_su13.save()

        self.tz = timezone.get_current_timezone()
        date = make_aware(datetime.datetime(2012, 02, 01), self.tz)
        self.season_12 = Season.objects.get_current_season(date)

        date = make_aware(datetime.datetime(2013, 02, 01), self.tz)
        self.season_13 = Season.objects.get_current_season(date)

    def test_get_corresponding_term(self):
        # Note that this method first checks the current Term, and returns it
        # if the current Term is during this PiE Season. Otherwise the method
        # finds the term nearest to Spring that exists for this Season

        self.term_fa12.current = True
        self.term_fa12.save()

        # 2012 Season:
        # Maps to Spring 2012 Term (since sp12 exists, and the current term is
        # part of a different Season)
        self.assertEqual(self.season_12.get_corresponding_term(),
                         self.term_sp12)

        # 2013 Season:
        # When Fall 2012 is current:
        self.assertEqual(self.season_13.get_corresponding_term(),
                         self.term_fa12)
        # When Summer 2012 is current:
        self.term_fa12.current = False
        self.term_fa12.save()
        self.term_su12.current = True
        self.term_su12.save()
        self.assertEqual(self.season_13.get_corresponding_term(),
                         self.term_su12)
        # When a term not in the 2013 Season is current:
        self.term_su12.current = False
        self.term_su12.save()
        self.term_su13.current = True
        self.term_su13.save()
        self.assertEqual(self.season_13.get_corresponding_term(),
                         self.term_sp13)

        # 2015 Season:
        date = make_aware(datetime.datetime(2015, 02, 01), self.tz)
        season = Season.objects.get_current_season(date)
        # When no Term exists that is in the current season:
        self.assertEqual(season.get_corresponding_term(), None)

        # Add terms that are during the 2015 Season, and ensure that term
        # nearest to Spring is selected when the current term is not in this
        # season:
        term_su14 = Term(term=Term.SUMMER, year=2014)
        term_su14.save()
        self.assertEqual(season.get_corresponding_term(), term_su14)

        term_fa14 = Term(term=Term.FALL, year=2014)
        term_fa14.save()
        self.assertEqual(season.get_corresponding_term(), term_fa14)

        term_sp15 = Term(term=Term.SPRING, year=2015)
        term_sp15.save()
        self.assertEqual(season.get_corresponding_term(), term_sp15)

    def test_get_pie_season_from_term(self):
        # Check that all created terms map to the correct seasons:

        # Spring 2012 --> 2012 Season
        self.assertEqual(Season.get_pie_season_from_term(self.term_sp12),
                         self.season_12)
        self.assertNotEqual(Season.get_pie_season_from_term(self.term_sp12),
                            self.season_13)

        # Summer 2012 --> 2013 Season
        self.assertEqual(Season.get_pie_season_from_term(self.term_su12),
                         self.season_13)
        self.assertNotEqual(Season.get_pie_season_from_term(self.term_su12),
                            self.season_12)

        # Fall 2012 --> 2013 Season
        self.assertEqual(Season.get_pie_season_from_term(self.term_fa12),
                         self.season_13)
        self.assertNotEqual(Season.get_pie_season_from_term(self.term_su12),
                            self.season_12)

        # Spring 2013 --> 2013 Season
        self.assertEqual(Season.get_pie_season_from_term(self.term_sp13),
                         self.season_13)
        self.assertNotEqual(Season.get_pie_season_from_term(self.term_sp13),
                            self.season_12)

        # Summer 2013 --> 2014 Season
        # Season for 2014 does not yet exist, so it is created upon calling the
        # method:
        season = Season.get_pie_season_from_term(self.term_su13)
        self.assertEqual(season.year, 2014)
        self.assertNotEqual(Season.get_pie_season_from_term(self.term_su13),
                            self.season_12)
        self.assertNotEqual(Season.get_pie_season_from_term(self.term_su13),
                            self.season_13)


class SchoolTest(TestCase):
    def test_uniqueness(self):
        school = School(name='Testing High School',
                        street_number=1234, street='Test St.', city='Berkeley',
                        state='CA', zipcode=94704)
        school.save()
        duplicate_school = School(name='Testing High School',
                                  street_number=1234, street='Test St.',
                                  city='Berkeley', state='CA', zipcode=94704)
        self.assertRaises(IntegrityError, duplicate_school.save)


class TeamTest(TestCase):
    def test_friendly_name(self):
        school = School(name='Testing High School',
                        street_number=1234, street='Test St.', city='Berkeley',
                        state='CA', zipcode=94704)
        season = Season.objects.get_current_season()
        team = Team(number=1, name='Pink Team', school=school, season=season)
        self.assertEqual(team.friendly_name(), 'Team 1: Testing High School')


class PiEOfficerPositionTest(TestCase):
    """
    Test for initial data placed in the fixture folder of this
    directory. It verifies that we aren't having collisions between
    the primary keys of the different positions in TBP and PiE.
    """
    fixtures = ['../../base_tbp/fixtures/officer_position.yaml',
                'officer_position.yaml']

    def test_initial_data(self):
        num = len(OfficerPosition.objects.filter(
            position_type__gt=OfficerPosition.TBP_OFFICER))
        self.assertEquals(num, 26)

    def test_total_init_data(self):
        num = OfficerPosition.objects.count()
        self.assertEquals(num, 47)
