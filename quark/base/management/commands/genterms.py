import datetime
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from quark.base.models import Term


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            '-s', '--span', type='int', default=5,
            help='Generate terms from (year - span) to (year + span)'),
        make_option(
            '--summer', action='store_true', dest='summer', default=False,
            help='Generate summer terms also')
        )

    def handle(self, *args, **kwargs):
        """Create Term instances for current year +/-span(years) inclusive."""
        new_terms = generate_terms(
            span=kwargs.get('span', 5),
            include_summer=kwargs.get('summer', False))
        if int(kwargs.get('verbosity')) > 0:
            self.stdout.write('Created {} Terms'.format(len(new_terms)))
            for term in new_terms:
                self.stdout.write(' - {term}'.format(term=str(term)))


def generate_terms(span=5, include_summer=False):
    """Create Term instances for current year +/-span(years) inclusive."""
    current_year = datetime.date.today().year
    start_year = max(current_year - span, datetime.MINYEAR)
    end_year = min(current_year + span, datetime.MAXYEAR)

    term_codes = [Term.FALL, Term.SPRING]
    if include_summer:
        term_codes.append(Term.SUMMER)
    if settings.TERM_TYPE == 'quarter':
        term_codes.append(Term.WINTER)
    new_terms = []
    with transaction.atomic():
        existing_terms = set([t.id for t in Term.objects.filter(
            year__gte=start_year, year__lte=end_year)])
        for year in range(start_year, end_year + 1):
            for term in term_codes:
                new_term = Term(term=term, year=year)
                new_term.id = new_term._calculate_pk()
                if new_term.id not in existing_terms:
                    new_terms.append(new_term)
        Term.objects.bulk_create(new_terms)
    return new_terms
