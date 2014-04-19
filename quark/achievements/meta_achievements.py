from django.db import models

from quark.achievements.models import Achievement
from quark.achievements.models import UserAchievement
from quark.shortcuts import get_object_or_none


# achievement-related achievements
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


models.signals.post_save.connect(assign_completion_achievements,
                                 sender=UserAchievement)


models.signals.post_save.connect(assign_icon_achievements,
                                 sender=Achievement)
