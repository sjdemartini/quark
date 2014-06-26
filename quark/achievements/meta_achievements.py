from django.db import models

from quark.achievements.models import Achievement
from quark.achievements.models import UserAchievement
from quark.shortcuts import get_object_or_none


# achievement-related achievements
def assign_award_achievements(sender, instance, created, **kwargs):
    short_name_set = set(['cots', 'mots', 'oots'])

    # check if this achievement is OOTS, MOTS, or COTS
    if instance.achievement.short_name in short_name_set:
        # obtain the user's achievements in a list of short names
        user_achievements = UserAchievement.objects.select_related(
            'achievement__short_name').filter(
            user=instance.user, acquired=True).values_list(
            'achievement__short_name', flat=True)

        # encode in utf8 to remove unicode characters from strings
        user_achievements_set = set([short_name.encode('utf8')
                                    for short_name in user_achievements])

        # check if all short names in list are present in user's achievements
        if (len(short_name_set & user_achievements_set) ==
                len(short_name_set)):
            achievement = get_object_or_none(Achievement,
                                             short_name='cots_mots_oots')
            if achievement:
                achievement.assign(instance.user, term=instance.term)


def assign_completion_achievements(sender, instance, created, **kwargs):
    if instance.achievement.short_name != 'acquire_15_achievements':
        # count the number of acquired achievements for the user
        user_achievements = UserAchievement.objects.select_related(
            'term').filter(user=instance.user, acquired=True).order_by(
            'term__pk')

        achievement_count = user_achievements.count()

        # the number of acquired achievements to obtain these achievements
        benchmarks = [15]

        for benchmark in benchmarks:
            short_name = 'acquire_{:02d}_achievements'.format(benchmark)
            achievement = get_object_or_none(
                Achievement, short_name=short_name)
            if achievement:
                if achievement_count < benchmark:
                    achievement.assign(
                        instance.user,
                        acquired=False,
                        progress=achievement_count)
                else:
                    achievement.assign(
                        instance.user,
                        term=user_achievements[benchmark - 1].term)


def assign_icon_achievements(sender, instance, created, **kwargs):
    if instance.icon_creator:
        # count the number of achievements with icons created by the user
        achievements = Achievement.objects.filter(
            icon_creator=instance.icon_creator)

        achievement_count = achievements.count()

        # the number of icons created to obtain achievements
        benchmarks = [1, 5]

        for benchmark in benchmarks:
            short_name = 'create_{:02d}_icons'.format(benchmark)
            achievement = get_object_or_none(Achievement, short_name=short_name)
            if achievement:
                if achievement_count < benchmark:
                    achievement.assign(
                        instance.icon_creator,
                        acquired=False,
                        progress=achievement_count)
                else:
                    achievement.assign(instance.icon_creator)


models.signals.post_save.connect(assign_award_achievements,
                                 sender=UserAchievement)


models.signals.post_save.connect(assign_completion_achievements,
                                 sender=UserAchievement)


models.signals.post_save.connect(assign_icon_achievements,
                                 sender=Achievement)
