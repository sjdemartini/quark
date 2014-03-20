import datetime

from django.test import TransactionTestCase
from django.test.utils import override_settings

from quark.base.models import Term
from quark.base.management.commands.genterms import generate_terms


class GenerateTermsTest(TransactionTestCase):
    @override_settings(TERM_TYPE='quarter')
    def test_generate_terms_quarter_plus_summer(self):
        self.assertFalse(Term.objects.all().exists())
        current_year = datetime.date.today().year
        terms_per_year = 4
        span_years = 1
        num_terms_generated = (2 * span_years + 1) * terms_per_year
        terms = generate_terms(
            span=span_years, include_summer=True)
        self.assertEqual(current_year - span_years, terms[0].year)
        self.assertEqual(current_year + span_years, terms[-1].year)
        self.assertEqual(Term.objects.all().count(), num_terms_generated)
        self.assertFalse(Term.objects.filter(current=True).exists())
        # Save test time, leave further tests for semester

    @override_settings(TERM_TYPE='semester')
    def test_generate_terms_semester(self):
        self.assertFalse(Term.objects.all().exists())
        current_year = datetime.date.today().year
        terms_per_year = 2
        span_years = 1
        num_terms_generated = (2 * span_years + 1) * terms_per_year
        terms = generate_terms(span=span_years)
        self.assertEqual(current_year - span_years, terms[0].year)
        self.assertEqual(current_year + span_years, terms[-1].year)
        self.assertEqual(Term.objects.all().count(), num_terms_generated)
        self.assertEqual(len(terms), num_terms_generated)
        self.assertFalse(Term.objects.filter(current=True).exists())

        # Prepare further testing
        current_term = Term.objects.get(term=Term.SPRING, year=2014)
        current_term.current = True
        current_term.save()
        self.assertEqual(current_term, Term.objects.get_current_term())

        # Generate more terms
        span_years2 = 3
        num_terms_generated2 = 2 * (span_years2 - span_years) * terms_per_year
        terms = generate_terms(span=span_years2)
        self.assertEqual(current_year - span_years2, terms[0].year)
        self.assertEqual(current_year + span_years2, terms[-1].year)
        self.assertEqual(len(terms), num_terms_generated2)
        self.assertEqual(
            Term.objects.all().count(),
            num_terms_generated + num_terms_generated2)
        self.assertEqual(current_term, Term.objects.get_current_term())
