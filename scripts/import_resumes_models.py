from dateutil import parser
from django.contrib.auth import get_user_model
from django.core.files import File
from django.utils.timezone import get_current_timezone
from django.utils.timezone import make_aware

from quark.resumes.models import Resume

from scripts import get_json_data
from scripts import NOIRO_MEDIA_LOCATION


user_model = get_user_model()
timezone = get_current_timezone()


def import_resumes():
    models = get_json_data('user_profiles.resume.json')
    for model in models:
        fields = model['fields']
        user = user_model.objects.get(pk=fields['user'])

        resume, _ = Resume.objects.get_or_create(
            pk=model['pk'],
            user=user,
            gpa=fields['gpa'],
            full_text=fields['full_text'],
            verified=fields['approved'],
            critique=fields['critique_requested'],
            release=fields['release'])

        # Convert the naive datetime into an aware datetime
        created = parser.parse(fields['timestamp'])
        resume.created = make_aware(created, timezone)
        resume.save()

        # Try to get the resume file, which may not exist (very rare)
        try:
            with open(NOIRO_MEDIA_LOCATION +
                      fields['file'], 'r') as resume_file:
                resume.resume_file = File(resume_file)
                resume.save()
        except IOError:
            print('Could not import {}\'s resume.'.format(user))
