from django.db import models

from quark.achievements.models import Achievement
from quark.base.models import Officer
from quark.shortcuts import get_object_or_none


# officership-related achievements
def officership_achievements(sender, instance, created, **kwargs):
    officerships = Officer.objects.filter(user=instance.user).exclude(
        position__short_name='advisor').exclude(
        position__short_name='faculty').order_by(
        'term__year', '-term__term')

    # unique officer semesters in case someone is multiple positions in
    # same semesters
    unique_terms = []
    unique_chair_committees = {'committees': [], 'terms': []}
    for officership in officerships:
        if officership.term not in unique_terms:
            unique_terms.append(officership.term)
        if (officership.is_chair and officership.position not in
                unique_chair_committees['committees']):
            unique_chair_committees['committees'].append(officership.position)
            unique_chair_committees['terms'].append(officership.term)

    # assign the achievements and progresses
    assign_tenure_achievements(instance, unique_terms)
    assign_chair_achievements(instance, unique_chair_committees)


def assign_tenure_achievements(instance, unique_terms):
    # 1 to 8 officer semesters
    num_unique_terms = len(unique_terms)
    for i in range(1, 9):
        short_name = 'officersemester{:02d}'.format(i)
        achievement = get_object_or_none(Achievement, short_name=short_name)
        if achievement:
            if num_unique_terms < i:
                achievement.assign(
                    instance.user, acquired=False, progress=num_unique_terms)
            else:
                achievement.assign(instance.user, term=unique_terms[i-1])


def assign_chair_achievements(instance, unique_chair_committees):
    num_committees_chaired = len(unique_chair_committees['committees'])
    chair1achievement = get_object_or_none(
        Achievement, short_name='chair1committee')
    chair2achievement = get_object_or_none(
        Achievement, short_name='chair2committees')
    if num_committees_chaired >= 1:
        if chair1achievement:
            chair1achievement.assign(
                instance.user, term=unique_chair_committees['terms'][0])

        if chair2achievement:
            if num_committees_chaired >= 2:
                chair2achievement.assign(
                    instance.user, term=unique_chair_committees['terms'][1])
            else:
                chair2achievement.assign(
                    instance.user, acquired=False, progress=1)

models.signals.post_save.connect(officership_achievements, sender=Officer)
