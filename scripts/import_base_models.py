import json
import os

from django.conf import settings

from quark.base.models import Term

# Dictionary mapping the pk's of noiro Semesters to the pk's of quark Terms.
# This is necessary for other models that have a foreign key to Term/Semester.
# Because the json files store foreign keys as just pk's, it's impossible
# to lookup the noiro Semester from the pk in the json file and then determine
# what the quark Term pk should be.
SEMESTER_TO_TERM = {}


def import_terms():
    data_path = os.path.join(
        settings.WORKSPACE_ROOT, 'scripts', 'data', 'noiro_main.semester.json')
    terms = json.load(open(data_path, 'r'))
    for term in terms:
        fields = term['fields']
        Term.objects.get_or_create(
            term=fields['semester'],
            year=fields['year'],
            current=fields['current'])
        SEMESTER_TO_TERM[term['pk']] = (
            fields['year'] * 10 + Term.TERM_MAPPING[fields['semester']])
