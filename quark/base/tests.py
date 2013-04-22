from test.test_support import EnvironmentVarGuard
from test.test_support import import_fresh_module
import datetime
import uuid

from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone
from django.utils.timezone import make_aware
import mox

from quark.base import fields
from quark.base.models import RandomToken
from quark.base.models import Major
from quark.base.models import Term
from quark.base.models import University
from quark.settings.dev import DATABASES as DEV_DB
from quark.settings.production import DATABASES as PROD_DB
from quark.settings.staging import DATABASES as STAGING_DB


class RandomTokenManagerTest(TestCase):
    def setUp(self):
        self.mox = mox.Mox()
        self.tz = timezone.get_current_timezone()

    def tearDown(self):
        self.mox.UnsetStubs()

    def test_random_token_generate(self):
        date = make_aware(datetime.datetime(2012, 01, 01), self.tz)
        self.mox.StubOutWithMock(uuid, 'uuid4')
        uuid.uuid4().AndReturn('abcdefghijklmnopqrstuvwxyz')
        self.mox.ReplayAll()
        token = RandomToken.objects.generate(expiration_date=date)
        self.assertEqual(token.token, 'abcdefghijklmnopqrstuvwxyz')
        self.mox.VerifyAll()


class RandomTokenTest(TestCase):
    def setUp(self):
        self.mox = mox.Mox()
        self.tz = timezone.get_current_timezone()

    def tearDown(self):
        self.mox.UnsetStubs()

    def test_is_expired_false(self):
        date = make_aware(datetime.datetime(2012, 01, 01), self.tz)
        self.mox.StubOutWithMock(timezone, 'now')
        timezone.now().MultipleTimes().AndReturn(
            make_aware(datetime.datetime(2011, 01, 01), self.tz))
        self.mox.ReplayAll()
        token = RandomToken.objects.generate(expiration_date=date)
        self.assertFalse(token.is_expired())
        self.mox.VerifyAll()

    def test_is_expired(self):
        date = make_aware(datetime.datetime(2012, 01, 01), self.tz)
        self.mox.StubOutWithMock(timezone, 'now')
        timezone.now().MultipleTimes().AndReturn(
            make_aware(datetime.datetime(2013, 01, 01), self.tz))
        self.mox.ReplayAll()
        token = RandomToken.objects.generate(expiration_date=date)
        self.assertTrue(token.is_expired())
        self.mox.VerifyAll()


class MajorTest(TestCase):
    fixtures = ['major.yaml', 'university.yaml']

    def test_initial_number(self):
        num = Major.objects.count()
        self.assertEqual(num, 14)

    def test_uniqueness(self):
        ucb = University.objects.get(short_name='UCB')
        duplicate = Major(
            short_name='math',
            long_name='Math',
            university=ucb,
            website='http://math.berkeley.edu')
        with self.assertRaises(IntegrityError):
            duplicate.save()
        self.assertEqual(
            1,
            len(Major.objects.filter(
                short_name='math',
                long_name='Math',
                university=ucb,
                website='http://math.berkeley.edu')))


class TermManagerTest(TestCase):
    def test_get_current_term(self):
        Term(term=Term.SPRING, year=2012, current=False).save()
        Term(term=Term.FALL, year=2012, current=True).save()
        term = Term.objects.get_current_term()
        self.assertEquals(term.term, Term.FALL)
        self.assertEquals(term.year, 2012)

    def test_get_current_term_undefined(self):
        Term(term=Term.SPRING, year=2012, current=False).save()
        Term(term=Term.FALL, year=2012, current=False).save()
        term = Term.objects.get_current_term()
        self.assertIsNone(term)

    def test_get_terms(self):
        # Intentionally unordered.
        Term(term=Term.FALL, year=2011, current=False).save()
        Term(term=Term.SUMMER, year=2012, current=True).save()
        Term(term=Term.SPRING, year=2012, current=False).save()
        Term(term=Term.SPRING, year=2011, current=False).save()

        terms = Term.objects.get_terms(include_summer=True)

        self.assertEquals(len(terms), 4)

        self.assertEquals(terms[0].year, 2011)
        self.assertEquals(terms[0].term, Term.SPRING)

        self.assertEquals(terms[1].year, 2011)
        self.assertEquals(terms[1].term, Term.FALL)

        self.assertEquals(terms[2].year, 2012)
        self.assertEquals(terms[2].term, Term.SPRING)

        self.assertEquals(terms[3].year, 2012)
        self.assertEquals(terms[3].term, Term.SUMMER)
        self.assertTrue(terms[3].current)

    def test_get_terms_reversed(self):
        # Intentionally unordered.
        Term(term=Term.FALL, year=2011, current=False).save()
        Term(term=Term.SUMMER, year=2012, current=True).save()
        Term(term=Term.SPRING, year=2012, current=False).save()
        Term(term=Term.SPRING, year=2011, current=False).save()

        terms = Term.objects.get_terms(
            include_summer=True, reverse=True)

        self.assertEquals(len(terms), 4)

        self.assertEquals(terms[0].year, 2012)
        self.assertEquals(terms[0].term, Term.SUMMER)
        self.assertTrue(terms[0].current)

        self.assertEquals(terms[1].year, 2012)
        self.assertEquals(terms[1].term, Term.SPRING)

        self.assertEquals(terms[2].year, 2011)
        self.assertEquals(terms[2].term, Term.FALL)

        self.assertEquals(terms[3].year, 2011)
        self.assertEquals(terms[3].term, Term.SPRING)

    def test_get_terms_no_summer(self):
        # Intentionally unordered.
        Term(term=Term.SUMMER, year=2012, current=True).save()
        Term(term=Term.FALL, year=2011, current=False).save()
        Term(term=Term.SPRING, year=2012, current=False).save()
        Term(term=Term.FALL, year=2012, current=False).save()

        terms = Term.objects.get_terms(
            include_future=True, include_summer=False)

        self.assertEquals(len(terms), 3)

        self.assertEquals(terms[0].year, 2011)
        self.assertEquals(terms[0].term, Term.FALL)

        self.assertEquals(terms[1].year, 2012)
        self.assertEquals(terms[1].term, Term.SPRING)

        self.assertEquals(terms[2].year, 2012)
        self.assertEquals(terms[2].term, Term.FALL)

    def test_get_terms_no_future(self):
        # Intentionally unordered.
        Term(term=Term.SUMMER, year=2012, current=False).save()
        Term(term=Term.FALL, year=2011, current=False).save()
        Term(term=Term.FALL, year=2012, current=False).save()
        Term(term=Term.SPRING, year=2012, current=True).save()

        terms = Term.objects.get_terms()

        self.assertEquals(len(terms), 2)

        self.assertEquals(terms[0].year, 2011)
        self.assertEquals(terms[0].term, Term.FALL)

        self.assertEquals(terms[1].year, 2012)
        self.assertEquals(terms[1].term, Term.SPRING)

    @override_settings(TERM_TYPE='quarter')
    def test_get_terms_quarter(self):
        # Intentionally unordered.
        Term(term=Term.WINTER, year=2012, current=True).save()

        terms = Term.objects.get_terms()

        self.assertEquals(len(terms), 1)

        self.assertEquals(terms[0].year, 2012)
        self.assertEquals(terms[0].term, Term.WINTER)

    @override_settings(TERM_TYPE='semester')
    def test_get_terms_semester(self):
        # Intentionally unordered.
        Term(term=Term.WINTER, year=2012, current=True).save()

        terms = Term.objects.get_terms()

        self.assertEquals(len(terms), 0)

    def test_get_terms_empty(self):
        terms = Term.objects.get_terms()
        self.assertEquals(len(terms), 0)

    def test_get_by_url_name(self):
        Term(term=Term.FALL, year=2012, current=True).save()
        term = Term.objects.get_by_url_name('fa2012')
        self.assertEquals(term.year, 2012)
        self.assertEquals(term.term, Term.FALL)
        self.assertTrue(term.current)

    def test_get_by_url_name_does_not_exist(self):
        term = Term.objects.get_by_url_name('fa2012')
        self.assertIsNone(term)

    def test_get_by_url_name_garbage(self):
        term = Term.objects.get_by_url_name('asdfasdf')
        self.assertIsNone(term)

    def test_get_by_url_name_empty(self):
        term = Term.objects.get_by_url_name('')
        self.assertIsNone(term)

    def test_get_by_url_name_not_string(self):
        term = Term.objects.get_by_url_name(5)
        self.assertIsNone(term)

    def test_get_by_natural_key(self):
        Term(term=Term.FALL, year=2012, current=True).save()
        term = Term.objects.get_by_natural_key(Term.FALL, 2012)
        self.assertEquals(term.year, 2012)
        self.assertEquals(term.term, Term.FALL)
        self.assertTrue(term.current)

    def test_get_by_natural_key_does_not_exist(self):
        term = Term.objects.get_by_natural_key(Term.FALL, 2012)
        self.assertIsNone(term)


class TermTest(TestCase):
    def test_save(self):
        spring = Term(term=Term.SPRING, year=2012, current=False)
        spring.save()
        fall = Term(term=Term.FALL, year=2012, current=False)
        fall.save()

        self.assertFalse(Term.objects.filter(current=True).exists())

        spring.current = True
        spring.save()
        current = Term.objects.filter(current=True)
        self.assertEquals(len(current), 1)
        self.assertEquals(current[0].year, 2012)
        self.assertEquals(current[0].term, Term.SPRING)

        fall.current = True
        fall.save()
        current = Term.objects.filter(current=True)
        self.assertEquals(len(current), 1)
        self.assertEquals(current[0].year, 2012)
        self.assertEquals(current[0].term, Term.FALL)

    def test_save_bad_pk(self):
        term = Term(term=Term.SPRING, year=2012, current=False)
        term.save()

        self.assertEquals(term.pk, 20122)
        self.assertEquals(term.year, 2012)
        self.assertEquals(term.term, Term.SPRING)

        term.year = 2013
        self.assertRaisesMessage(
            ValueError,
            ('You cannot update the year or term without '
             'also updating the primary key value.'),
            term.save)

        terms = Term.objects.all()
        self.assertEquals(len(terms), 1)
        term = terms[0]

        self.assertEquals(term.pk, 20122)
        self.assertEquals(term.year, 2012)
        self.assertEquals(term.term, Term.SPRING)

    def test_save_invalid_term(self):
        spring = Term(term=Term.UNKNOWN, year=0, current=True)
        spring.save()
        self.assertFalse(Term.objects.filter(current=True).exists())

    def test_unicode(self):
        term = Term(term=Term.FALL, year=2012, current=False)
        self.assertEqual(unicode(term), 'Fall 2012')

    def test_unicode_current(self):
        term = Term(term=Term.FALL, year=2012, current=True)
        self.assertEqual(unicode(term), 'Fall 2012 (Current)')

    def test_verbose_name(self):
        term = Term(term=Term.FALL, year=2012, current=False)
        self.assertEqual(term.verbose_name(), 'Fall 2012')

    def test_verbose_name_current(self):
        term = Term(term=Term.FALL, year=2012, current=True)
        self.assertEqual(term.verbose_name(), 'Fall 2012')

    def test_get_url_name(self):
        term = Term(term=Term.WINTER, year=2012, current=True)
        self.assertEqual(term.get_url_name(), 'wi2012')

        term = Term(term=Term.SPRING, year=2012, current=True)
        self.assertEqual(term.get_url_name(), 'sp2012')

        term = Term(term=Term.SUMMER, year=2012, current=True)
        self.assertEqual(term.get_url_name(), 'su2012')

        term = Term(term=Term.FALL, year=2012, current=True)
        self.assertEqual(term.get_url_name(), 'fa2012')

        term = Term(term=Term.UNKNOWN, year=2012, current=True)
        self.assertEqual(term.get_url_name(), 'un2012')

    def test_comparisons(self):
        fall = Term(term=Term.FALL, year=2012)
        spring = Term(term=Term.SPRING, year=2012)
        self.assertTrue(spring < fall)
        self.assertTrue(spring <= fall)
        self.assertFalse(spring > fall)
        self.assertFalse(spring >= fall)
        self.assertTrue(fall <= fall)
        self.assertTrue(fall >= fall)

    def test_garbage_comparisons(self):
        term = Term(term=Term.FALL, year=1900)
        self.assertTrue(term < 'foo')
        self.assertTrue(term <= 'foo')
        self.assertFalse(term > 'foo')
        self.assertFalse(term >= 'foo')
        self.assertTrue(term != 'foo')
        self.assertFalse(term == 'foo')

    def test_equality(self):
        one = Term(term=Term.FALL, year=2012)
        two = Term(term=Term.FALL, year=2012)
        self.assertTrue(one == two)

    def test_inequality(self):
        spring = Term(term=Term.SPRING, year=2012)
        fall = Term(term=Term.FALL, year=2012)
        self.assertTrue(spring != fall)

    def test_natural_key(self):
        term = Term(term=Term.SPRING, year=2012)
        self.assertEqual(term.natural_key(), (Term.SPRING, 2012))


class UniversityTest(TestCase):
    fixtures = ['university.yaml']

    def test_initial_number(self):
        num = University.objects.count()
        self.assertEquals(num, 1)


class SettingsTest(TestCase):
    def setUp(self):
        self.env = EnvironmentVarGuard()

    def test_unset(self):
        with self.env:
            self.env.set('QUARK_ENV', 'dev')
            settings = import_fresh_module('quark.settings')

            self.assertTrue(settings.DEBUG)
            self.assertEqual(settings.DATABASES, DEV_DB)

    def test_production(self):
        with self.env:
            self.env.set('QUARK_ENV', 'production')
            settings = import_fresh_module('quark.settings')

            self.assertFalse(settings.DEBUG)
            self.assertEqual(settings.DATABASES, PROD_DB)

    def test_staging(self):
        with self.env:
            self.env.set('QUARK_ENV', 'staging')
            settings = import_fresh_module('quark.settings')

            self.assertFalse(settings.DEBUG)
            self.assertEqual(settings.DATABASES, STAGING_DB)


class FieldsTest(TestCase):
    def setUp(self):
        self.visual_dt_field = fields.VisualSplitDateTimeField()

    def test_visual_split_datetime(self):
        # Ensure that the proper widget is used:
        widget = self.visual_dt_field.widget
        self.assertTrue(isinstance(widget, fields.VisualSplitDateTimeWidget))

        # Test that the appropriate HTML classes are set for the input fields:
        self.assertEqual(widget.widgets[0].attrs['class'], 'vDateField')
        self.assertEqual(widget.widgets[1].attrs['class'], 'vTimeField')

        # Get the time field (since SplitDatetimeField has a DateField and a
        # TimeField):
        time_field = self.visual_dt_field.fields[1]

        # Check that the proper time formats are allowed by performing
        # to_python() on inputs, which raises a Violation if an improper format
        # is used:
        self.assertIsNotNone(time_field.to_python('03:14am'))
        self.assertIsNotNone(time_field.to_python('1:11am'))
        self.assertIsNotNone(time_field.to_python('05:00 pm'))
        self.assertIsNotNone(time_field.to_python('11:11pm'))

        # 24 hour format not allowed:
        self.assertRaises(ValidationError, time_field.to_python, '23:11')
        # Needs am/pm:
        self.assertRaises(ValidationError, time_field.to_python, '3:14')
        # Must use colon delimiter:
        self.assertRaises(ValidationError, time_field.to_python, '5.30')
