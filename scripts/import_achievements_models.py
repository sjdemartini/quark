from django.contrib.auth import get_user_model

from quark.achievements.models import Achievement
from quark.achievements.models import UserAchievement
from quark.base.models import Term
from scripts import get_json_data
from scripts.import_base_models import SEMESTER_TO_TERM


ACHIEVEMENT_CONVERSION = {
    37: 'oots',
    38: 'cots',
    39: 'mots',
    25: 'write_code',
    42: 'lead_house_to_win',
    66: 'rock',
    41: 'bowling_pin',
    29: 'tbp_romance',
    16: 'attend_all_oms',
    17: 'attend_all_ems',
    63: 'banquet_errands',
    64: 'reply_all',
    30: 'create_01_icons',
    59: 'create_05_icons'
}


user_model = get_user_model()


def import_user_achievements():
    models = get_json_data('achievements.userachievement.json')
    for model in models:
        fields = model['fields']

        achievement = ACHIEVEMENT_CONVERSION.get(fields['achievement'])
        if achievement:
            user_achievement, _ = UserAchievement.objects.get_or_create(
                user=user_model.objects.get(pk=fields['user']),
                achievement=Achievement.objects.get(short_name=achievement),
                acquired=True,
                term=Term.objects.get(pk=SEMESTER_TO_TERM[fields['semester']]),
                data=fields['data'])

            assigner = fields['assigner']
            if assigner:
                user_achievement.assigner = user_model.objects.get(pk=assigner)
                user_achievement.save()
