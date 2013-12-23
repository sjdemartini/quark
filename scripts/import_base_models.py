from django.contrib.auth import get_user_model

from quark.base.models import Officer
from quark.base.models import OfficerPosition
from quark.base.models import Term
from scripts import get_json_data


# Dictionary mapping the pk's of noiro Semesters to the pk's of quark Terms.
# This is necessary for other models that have a foreign key to Term/Semester.
# Because the json files store foreign keys as just pk's, it's impossible
# to lookup the noiro Semester from the pk in the json file and then determine
# what the quark Term pk should be.
SEMESTER_TO_TERM = {}


def import_terms():
    models = get_json_data('noiro_main.semester.json')
    for model in models:
        fields = model['fields']
        term, _ = Term.objects.get_or_create(
            term=fields['semester'],
            year=fields['year'],
            current=fields['current'])
        SEMESTER_TO_TERM[model['pk']] = term.pk


user_model = get_user_model()


def import_officers():
    models = get_json_data('noiro_main.officer.json')
    for model in models:
        fields = model['fields']
        Officer.objects.get_or_create(
            pk=model['pk'],
            user=user_model.objects.get(pk=fields['user']),
            position=OfficerPosition.objects.get(pk=fields['position']),
            term=Term.objects.get(pk=SEMESTER_TO_TERM[fields['semester']]),
            is_chair=fields['is_chair'])
