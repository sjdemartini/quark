import string

from django.db import models

from quark.achievements.models import Achievement
from quark.project_reports.models import ProjectReport
from quark.shortcuts import get_object_or_none


def project_report_achievements(sender, instance, created, **kwargs):
    # only check the achievement assignment if the PR is complete
    if instance.complete:
        assign_alphabet_pr_achievement(instance)
        assign_lifetime_pr_achievements(instance)
        assign_procrastination_achievement(instance)


def assign_alphabet_pr_achievement(instance):
    # see if letters A-Z are in project report text
    project_report_text = ''.join([instance.title,
                                   instance.other_group,
                                   instance.description,
                                   instance.purpose,
                                   instance.organization,
                                   instance.cost,
                                   instance.problems,
                                   instance.results])
    unused_letters = set(string.lowercase)
    unused_letters.difference_update(project_report_text.lower())

    if len(unused_letters) == 0:
        achievement = get_object_or_none(Achievement,
                                         short_name='alphabet_project_report')
        if achievement:
            achievement.assign(instance.author, term=instance.term)


def assign_lifetime_pr_achievements(instance):
    # obtain all project reports authored by user
    project_reports = ProjectReport.objects.select_related(
        'event__term').filter(
        author=instance.author, complete=True).order_by('event__term__pk')

    project_report_count = project_reports.count()

    # the number of project reports needed to get achievements
    benchmarks = [1, 5, 15]

    for benchmark in benchmarks:
        short_name = 'write_{:02d}_project_reports'.format(benchmark)
        achievement = get_object_or_none(Achievement, short_name=short_name)
        if achievement:
            if project_report_count < benchmark:
                achievement.assign(
                    instance.author, acquired=False,
                    progress=project_report_count)
            else:
                achievement.assign(
                    instance.author,
                    term=project_reports[benchmark - 1].term)


def assign_procrastination_achievement(instance):
    # obtain the time taken to write the project report (the date between
    # the event date and the first completed date)
    event_date = instance.date
    completion_date = instance.first_completed_at.date()
    writing_time = completion_date - event_date

    if writing_time.days >= 60:
        achievement = get_object_or_none(
            Achievement, short_name='project_report_procrastination')
        if achievement:
            achievement.assign(instance.author, term=instance.term)


models.signals.post_save.connect(project_report_achievements,
                                 sender=ProjectReport)
