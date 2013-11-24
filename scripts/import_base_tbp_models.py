from django.contrib.auth import get_user_model

from quark.base.models import Term
from quark.base_tbp.models import Officer
from quark.base_tbp.models import OfficerPosition

from scripts import get_json_data
from scripts.import_base_models import SEMESTER_TO_TERM


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
