from dateutil import parser
from django.contrib.auth import get_user_model
from django.utils.timezone import get_current_timezone
from django.utils.timezone import make_aware

from quark.base.models import Term
from quark.minutes.models import Minutes
from scripts import get_json_data
from scripts.import_base_models import SEMESTER_TO_TERM


user_model = get_user_model()
timezone = get_current_timezone()


def import_minutes():
    models = get_json_data('minutes.minutes.json')
    for model in models:
        fields = model['fields']

        # Determine the meeting type based off the name
        name = fields['name']
        if (name == 'OM' or ' OM' in name or 'officer meeting' in name.lower()):
            meeting_type = Minutes.OFFICER
        elif (name == 'EM' or ' EM' in name or 'exec meeting' in name.lower()):
            meeting_type = Minutes.EXEC
        else:
            meeting_type = Minutes.OTHER

        minutes, _ = Minutes.objects.get_or_create(
            pk=model['pk'],
            name=name,
            date=fields['date'],
            term=Term.objects.get(pk=SEMESTER_TO_TERM[fields['semester']]),
            meeting_type=meeting_type,
            notes=fields['notes'],
            public=fields['public'],
            author=user_model.objects.get(pk=fields['poster']))

        # Convert the naive datetime into an aware datetime
        updated = parser.parse(fields['updated'])
        minutes.updated = make_aware(updated, timezone)
        minutes.save()
