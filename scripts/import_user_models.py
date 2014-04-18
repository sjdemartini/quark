import os

from dateutil import parser
from django.contrib.auth import get_user_model
from django.core.files import File
from django.utils.timezone import get_current_timezone
from django.utils.timezone import make_aware

from quark.base.models import Major
from quark.base.models import Term
from quark.user_profiles.models import CollegeStudentInfo
from quark.user_profiles.models import StudentOrgUserProfile
from quark.user_profiles.models import UserProfile
from scripts import get_json_data
from scripts import NOIRO_MEDIA_LOCATION
from scripts.import_base_models import SEMESTER_TO_TERM


# The pk's for Major start at 1 in noiro and 1000 in quark. The ordering of
# the majors is the same, so 999 needs to be added to a noiro pk to convert it
# to a quark pk.
MAJOR_PK_CONVERSION = 999
# Dictionary mapping the pk's of users to booleans of whether they have
# initiated. This is necessary when importing candidates because has_initiated
# was moved from the user profile model to the candidate model, and it's
# impossible to lookup has_initiated from the json file given a candidate or
# user pk.
HAS_INITIATED = {}

user_model = get_user_model()
timezone = get_current_timezone()


def delete_users():
    user_model.objects.all().delete()


def delete_user_profiles():
    UserProfile.objects.all().delete()


def import_users():
    models = get_json_data('auth.user.json')
    for model in models:
        fields = model['fields']
        user = user_model.objects.create_user(
            pk=model['pk'],
            username=fields['username'],
            email=fields['email'])
        user.first_name = fields['first_name']
        user.last_name = fields['last_name']
        user.is_active = fields['is_active']
        user.is_superuser = fields['is_superuser']
        user.is_staff = fields['is_staff']
        user.email = fields['email']

        # Convert the naive datetime into an aware datetime
        date_joined = parser.parse(fields['date_joined'])
        user.date_joined = make_aware(date_joined, timezone)

        user.save()


def import_user_profiles():
    # pylint: disable=E1103
    models = get_json_data('user_profiles.userprofile.json')
    for model in models:
        fields = model['fields']
        HAS_INITIATED[fields['user']] = fields['has_initiated']

        user_profile, _ = UserProfile.objects.get_or_create(
            pk=model['pk'],
            user=user_model.objects.get(pk=fields['user']),
            preferred_name=fields['preferred_name'],
            middle_name=fields['middle_name'],
            gender=fields['gender'],
            alt_email=fields['alt_email'],
            cell_phone=fields['cell_phone'],
            home_phone=fields['home_phone'],
            receive_text=fields['receive_text'],
            local_address1=fields['local_address1'],
            local_address2=fields['local_address2'],
            local_city=fields['local_city'],
            local_state=fields['local_state'],
            local_zip=fields['local_zip'],
            perm_address1=fields['perm_address1'],
            perm_address2=fields['perm_address2'],
            perm_city=fields['perm_city'],
            perm_state=fields['perm_state'],
            perm_zip=fields['perm_zip'],
            international_address=fields['international_address'])

        if fields['birthday']:
            user_profile.birthday = parser.parse(fields['birthday']).date()
            user_profile.save()

        if fields['picture']:
            picture_location = os.path.join(
                NOIRO_MEDIA_LOCATION, fields['picture'])
            with open(picture_location, 'r') as picture:
                user_profile.picture = File(picture)
                user_profile.save()

        student_info, _ = CollegeStudentInfo.objects.get_or_create(
            pk=model['pk'],
            user=user_model.objects.get(pk=fields['user']))
        for major_pk in fields['major']:
            student_info.major.add(Major.objects.get(
                pk=major_pk + MAJOR_PK_CONVERSION))
        if fields['start_semester']:
            student_info.start_term = Term.objects.get(
                pk=SEMESTER_TO_TERM[fields['start_semester']])
        if fields['grad_semester']:
            student_info.grad_term = Term.objects.get(
                pk=SEMESTER_TO_TERM[fields['grad_semester']])
        student_info.save()

        user = user_model.objects.get(pk=fields['user'])
        student_profile, _ = StudentOrgUserProfile.objects.get_or_create(
            pk=model['pk'], user=user, bio=fields['bio'])
        if fields['initiation_semester']:
            student_profile.initiation_term = Term.objects.get(
                pk=SEMESTER_TO_TERM[fields['initiation_semester']])
        student_profile.save()
