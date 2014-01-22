from dateutil import parser
from django.contrib.auth import get_user_model
from django.utils.timezone import get_current_timezone
from django.utils.timezone import make_aware
from pytz import AmbiguousTimeError

from quark.base.models import OfficerPosition
from quark.base.models import Term
from quark.events.models import Event
from quark.events.models import EventAttendance
from quark.events.models import EventSignUp
from quark.events.models import EventType
from quark.project_reports.models import ProjectReport
from scripts import get_json_data
from scripts.import_base_models import SEMESTER_TO_TERM


user_model = get_user_model()
timezone = get_current_timezone()


def import_event_types():
    models = get_json_data('events.eventtype.json')
    for model in models:
        fields = model['fields']
        EventType.objects.get_or_create(
            pk=model['pk'],
            name=fields['name'])


def import_events():
    models = get_json_data('events.event.json')
    for model in models:
        fields = model['fields']

        # Convert the naive datetimes into aware datetimes
        start_datetime = make_aware(
            parser.parse(fields['start_datetime']), timezone)
        end_datetime = make_aware(
            parser.parse(fields['end_datetime']), timezone)

        event, _ = Event.objects.get_or_create(
            pk=model['pk'],
            name=fields['name'],
            event_type=EventType.objects.get(pk=fields['event_type']),
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            term=Term.objects.get(pk=SEMESTER_TO_TERM[fields['semester']]),
            tagline=fields['tagline'],
            description=fields['description'],
            location=fields['location'],
            contact=user_model.objects.get(pk=fields['contact']),
            restriction=fields['restriction'],
            signup_limit=fields['signup_limit'],
            needs_drivers=fields['needs_drivers'],
            cancelled=fields['cancelled'],
            requirements_credit=fields['requirements_credit'])

        if fields['committee']:
            event.committee = OfficerPosition.objects.get(
                pk=fields['committee'])
        if fields['project_report']:
            event.project_report = ProjectReport.objects.get(
                pk=fields['project_report'])

        event.save()


def import_event_sign_ups():
    models = get_json_data('events.eventsignup.json')
    for model in models:
        fields = model['fields']
        pk = model['pk']

        event_sign_up, _ = EventSignUp.objects.get_or_create(
            pk=pk,
            event=Event.objects.get(pk=fields['event']),
            name=fields['name'],
            driving=fields['driving'],
            comments=fields['comments'],
            email=fields['email'],
            unsignup=fields['unsignup'])

        if fields['person']:
            event_sign_up.user = user_model.objects.get(pk=fields['person'])
        event_sign_up.save()

        try:
            # Try to convert the naive datetime into an aware datetime, which
            # may fail because of daylight savings time creating ambiguity for
            # some timestamps
            timestamp = make_aware(parser.parse(fields['timestamp']), timezone)

            # Get a queryset of the single object so that update can be called,
            # which doesn't call save and allows fields with auto_now=True to be
            # overridden
            event_sign_up = EventSignUp.objects.filter(pk=pk)
            event_sign_up.update(timestamp=timestamp)
        except AmbiguousTimeError:
            print('ERROR: Could not import timestamp for {}'.format(
                event_sign_up))


def import_event_attendances():
    models = get_json_data('events.eventattendance.json')
    for model in models:
        fields = model['fields']
        EventAttendance.objects.get_or_create(
            pk=model['pk'],
            event=Event.objects.get(pk=fields['event']),
            user=user_model.objects.get(pk=fields['person']))
