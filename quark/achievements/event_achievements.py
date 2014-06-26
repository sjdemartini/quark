import re
import string

from django.db import models

from quark.achievements.models import Achievement
from quark.base.models import Term
from quark.events.models import Event
from quark.events.models import EventAttendance
from quark.shortcuts import get_object_or_none


def event_achievements(sender, instance, created, **kwargs):
    # obtain lifetime attendance for the user
    total_attendance = EventAttendance.objects.select_related(
        'event__term').filter(
        user=instance.user, event__cancelled=False).order_by('event__term__pk')

    # obtain the events in the term that the edited event is in
    term_events = Event.objects.filter(
        cancelled=False, term=instance.event.term)

    # obtain the events that the user has attended in this term
    term_attendance = total_attendance.filter(
        event__term=instance.event.term).select_related(
        'term', 'event__event_type')

    # obtain the events in the term with the same type
    type_events = term_events.filter(event_type=instance.event.event_type)

    # sets of the event types attended and existing in the term to assign
    # the achievement for attending 1 event of each type
    types_attended = term_attendance.values('event__event_type').distinct()
    types_existing = term_events.values('event_type').distinct()

    # remaining letters to track the achievement for attending events with
    # the letters a-z in their titles in a term
    remaining_letters = set(string.lowercase)

    for event_attendance in term_attendance:
        remaining_letters.difference_update(
            event_attendance.event.name.lower())
        if len(remaining_letters) == 0:
            break

    assign_alphabet_achievement(instance, remaining_letters)
    assign_event_type_achievements(instance, type_events)
    assign_lifetime_achievements(instance, total_attendance)
    assign_salad_bowl_achievement(instance, types_attended, types_existing)
    assign_specific_event_achievements(instance)


def assign_alphabet_achievement(instance, remaining_letters):
    if len(remaining_letters) == 0:
        achievement = get_object_or_none(Achievement,
                                         short_name='alphabet_attendance')
        if achievement:
            achievement.assign(instance.user, term=instance.event.term)


def assign_event_type_achievements(instance, type_events):
    # obtain the user's attendance for events with the same type as instance
    type_attendance = EventAttendance.objects.filter(
        user=instance.user,
        event__event_type=instance.event.event_type,
        event__term=instance.event.term,
        event__cancelled=False)

    event_type = instance.event.event_type
    # a map from the name of the event_type to the name of the corresponding
    # achievement, for use in determining what achievement to update
    event_type_map = {
        'Meeting': 'meetings',
        'Big Social': 'big_socials',
        'Bent Polishing': 'bent_polishings',
        'Infosession': 'infosessions',
        'Community Service': 'service',
        'E Futures': 'efutures',
        'Fun': 'fun',
        'Professional Development': 'prodev'
        }

    if event_type.name in event_type_map:
        short_name = 'attend_all_{}'.format(
            event_type_map[instance.event.event_type.name])
        achievement = get_object_or_none(
            Achievement, short_name=short_name)
        if achievement and (type_events.count() == type_attendance.count()):
            achievement.assign(instance.user, term=instance.event.term)


def assign_lifetime_achievements(instance, total_attendance):
    attendance_count = total_attendance.count()

    # the number of events needed to get achievements
    benchmarks = [25, 50, 78, 100, 150, 200, 300]

    for benchmark in benchmarks:
        short_name = 'attend{:03d}events'.format(benchmark)
        achievement = get_object_or_none(Achievement, short_name=short_name)
        if achievement:
            if attendance_count < benchmark:
                achievement.assign(
                    instance.user, acquired=False, progress=attendance_count)
            else:
                achievement.assign(
                    instance.user,
                    term=total_attendance[benchmark - 1].event.term)


def assign_salad_bowl_achievement(instance, types_attended, types_existing):
    if types_attended.count() == types_existing.count():
        achievement = get_object_or_none(
            Achievement, short_name='attend_each_type')
        if achievement:
            achievement.assign(instance.user, term=instance.event.term)


def assign_specific_event_achievements(instance):
    d15_regex = re.compile(r'.*D(istrict)?[\s]?15.*')
    if d15_regex.match(instance.event.name):
        d15_achievement = get_object_or_none(Achievement,
                                             short_name='attend_d15')
        if d15_achievement:
            d15_achievement.assign(instance.user, term=instance.event.term)

    if 'National Convention' in instance.event.name:
        natl_achievement = get_object_or_none(Achievement,
                                              short_name='attend_convention')
        if natl_achievement:
            natl_achievement.assign(instance.user, term=instance.event.term)

    if 'Envelope Stuffing' in instance.event.name:
        envelope_achievement = get_object_or_none(
            Achievement, short_name='attend_envelope_stuffing')
        if envelope_achievement:
            envelope_achievement.assign(instance.user, term=instance.event.term)

    if instance.event.name == 'Candidate Meeting' and (
            instance.event.term == Term(term=Term.FALL, year=2013)):
        cm2013_achievement = get_object_or_none(
            Achievement, short_name='berkeley_explosion')
        if cm2013_achievement:
            cm2013_achievement.assign(instance.user, term=instance.event.term)


models.signals.post_save.connect(event_achievements, sender=EventAttendance)
