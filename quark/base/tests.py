from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings

from quark.base.models import Officer
from quark.base.models import OfficerPosition
from quark.base.models import Term


# pylint: disable-msg=R0904
class OfficerPositionTest(TestCase):
    def test_save(self):
        tbp_officer = OfficerPosition(
            position_type=OfficerPosition.TBP_OFFICER,
            short_name='IT',
            long_name='Information Technology',
            rank=2,
            mailing_list='IT')
        tbp_officer.save()

        self.assertFalse(
            OfficerPosition.objects.filter(
                position_type=OfficerPosition.PIE_COORD).exists())
        self.assertTrue(
            OfficerPosition.objects.filter(
                position_type=OfficerPosition.TBP_OFFICER).exists())
        pie_coord = OfficerPosition(
            position_type=OfficerPosition.TBP_OFFICER,
            short_name='PiE Coord',
            long_name='PiE Coordinatory',
            rank=3,
            mailing_list='PiE')
        pie_coord.save()

        positions = OfficerPosition.objects.order_by('position_type')
        self.assertEquals(len(positions), 2)
        self.assertEquals(positions[0].short_name, 'IT')
        self.assertEquals(positions[0].rank, 2)
        self.assertEquals(positions[1].short_name, 'PiE Coord')
        self.assertEquals(positions[1].rank, 3)


# pylint: disable-msg=R0904
class OfficerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'officer', 'it@tbp.berkeley.edu', 'officerpw')
        self.user.save()
        self.term = Term(term=Term.SPRING, year=2012, current=True)
        self.term.save()
        self.position = OfficerPosition(
            position_type=OfficerPosition.TBP_OFFICER,
            short_name='IT',
            long_name='Information Technology',
            rank=2,
            mailing_list='IT')
        self.position.save()

    def test_save(self):
        it_chair = Officer(user=self.user, position=self.position,
                           term=self.term, is_chair=True)
        it_chair.save()

        self.assertTrue(Officer.objects.filter(is_chair=True).exists())

        new_term = Term(term=Term.FALL, year=2011, current=False)
        new_term.save()
        it_officer = Officer(user=self.user, position=self.position,
                             term=new_term, is_chair=False)
        it_officer.save()
        officers = Officer.objects.filter(is_chair=True)

        self.assertEquals(len(officers), 1)
        self.assertEquals(officers[0].user, self.user)


# pylint: disable-msg=R0904
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


# pylint: disable-msg=R0904
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
