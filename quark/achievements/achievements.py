from django.db import models

from quark.achievements.models import Achievement
from quark.base_tbp.models import Officer


# officership-related achievements
def officership_achievements(sender, instance, created, **kwargs):
    officerships = Officer.objects.filter(user=instance.user).exclude(
        position__short_name='advisor').exclude(
        position__short_name='faculty').order_by(
        'term__year', '-term__term')

    # unique officer semesters in case someone is multiple positions in
    # same semesters
    unique_terms = []
    for officership in officerships:
        if officership.term not in unique_terms:
            unique_terms.append(officership.term)

    # assign the achievements and progressess for 1-8 officer semesters
    achievements_assigned = {'achievements': [], 'assigned': []}
    num_unique_terms = len(unique_terms)
    for i in range(1, 9):
        short_name = 'officersemester{:02d}'.format(i)
        if num_unique_terms < i:
            try:
                Achievement.objects.get(short_name=short_name).assign(
                    instance.user, acquired=False, progress=num_unique_terms)
                achievements_assigned['achievements'].append(short_name)
                achievements_assigned['assigned'].append(True)
            except Achievement.DoesNotExist:
                achievements_assigned['achievements'].append(short_name)
                achievements_assigned['assigned'].append(False)
        else:
            try:
                Achievement.objects.get(short_name=short_name).assign(
                    instance.user, short_name, term=unique_terms[i-1])
                achievements_assigned['achievements'].append(short_name)
                achievements_assigned['assigned'].append(True)
            except Achievement.DoesNotExist:
                achievements_assigned['achievements'].append(short_name)
                achievements_assigned['assigned'].append(False)

models.signals.post_save.connect(officership_achievements, sender=Officer)
