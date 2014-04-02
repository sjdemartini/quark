import collections

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

    # a list of unique officer terms in case someone is multiple positions in
    # same terms, to determine tenure achievements
    unique_terms = []

    # a dictionary mapping the user's officer position names to a list of the
    # terms in which those positions were held, for use in determining
    # the achievement for holding 3 different officer positions
    committee_terms = collections.OrderedDict()

    # a dictionary mapping the user's chair position names to a list of terms
    # in which the user was chair, to determine chairship achievements
    chair_terms = collections.OrderedDict()

    # a list of sequence dictionaries, to store each consecutive sequence of
    # the same officer position the user holds, for use in determining the
    # achievements for repeated officer positions
    repeat_positions = []
    previous_position = None
    sequence = {'positions': [], 'terms': []}

    for officership in officerships:
        position_name = officership.position.short_name

        if position_name in committee_terms:
            committee_terms[position_name].append(
                officership.term)
        else:
            committee_terms[position_name] = [officership.term]

        # compare this term to the most recent unique term
        if len(unique_terms) == 0 or officership.term != unique_terms[-1]:
            unique_terms.append(officership.term)

        if officership.is_chair:
            if position_name in chair_terms:
                chair_terms[position_name].append(
                    officership.term)
            else:
                chair_terms[position_name] = [officership.term]

        if position_name != previous_position:
            repeat_positions.append(sequence)

            sequence = {'positions': [], 'terms': []}
            sequence['positions'].append(position_name)
            sequence['terms'].append(officership.term)

            previous_position = position_name
        else:
            sequence['positions'].append(position_name)
            sequence['terms'].append(officership.term)

        # if the user has achieved vp in <=2 terms or president in <=3 terms
        # then assign the straight to the top achievement here to cover cases
        # where the user does both of these things
        num_unique_terms = len(unique_terms)
        if ((num_unique_terms <= 2 and position_name == 'vp') or
                (num_unique_terms <= 3 and position_name == 'president')):
            assign_straight_to_the_top_achievement(instance, officership.term)

    repeat_positions.append(sequence)

    # assign the achievements and progresses
    assign_tenure_achievements(instance, unique_terms)
    assign_chair_achievements(instance, chair_terms)
    assign_repeat_achievements(instance, repeat_positions)
    assign_diffposition_achievements(instance, committee_terms)


def assign_tenure_achievements(instance, unique_terms):
    num_unique_terms = len(unique_terms)

    # 1 to 8 officer semesters
    for i in range(1, 9):
        short_name = 'officersemester{:02d}'.format(i)
        achievement = get_object_or_none(Achievement, short_name=short_name)
        if achievement:
            if num_unique_terms < i:
                achievement.assign(
                    instance.user, acquired=False, progress=num_unique_terms)
            else:
                achievement.assign(instance.user, term=unique_terms[i-1])


def assign_chair_achievements(instance, chair_terms):
    num_committees_chaired = len(chair_terms)

    chair1achievement = get_object_or_none(
        Achievement, short_name='chair1committee')
    chair2achievement = get_object_or_none(
        Achievement, short_name='chair2committees')
    if num_committees_chaired >= 1:
        # terms is a list of lists
        terms = chair_terms.values()

        if chair1achievement:
            # for the first committee that was chaired, find the first term
            # that they were chair
            chair1_terms = terms[0]
            chair1achievement.assign(
                instance.user, term=chair1_terms[0])

        if chair2achievement:
            if num_committees_chaired >= 2:
                # for the second committee that was chaired, find the first
                # term that they were chair
                chair2_terms = terms[1]
                chair2achievement.assign(
                    instance.user, term=chair2_terms[0])
            else:
                chair2achievement.assign(
                    instance.user, acquired=False, progress=1)


def assign_repeat_achievements(instance, repeat_positions):
    twice_same_position = get_object_or_none(
        Achievement, short_name='twice_same_position')
    thrice_same_position = get_object_or_none(
        Achievement, short_name='thrice_same_position')
    two_repeated_positions = get_object_or_none(
        Achievement, short_name='two_repeated_positions')

    twice_held_positions = set()
    num_unique_twice_held_positions = 0

    for sequence in repeat_positions:
        if len(sequence['positions']) >= 2:
            if twice_same_position:
                twice_same_position.assign(
                    instance.user, term=sequence['terms'][1])

            if sequence['positions'][0] not in twice_held_positions:
                twice_held_positions.add(sequence['positions'][0])
                num_unique_twice_held_positions += 1

            if num_unique_twice_held_positions == 2:
                if two_repeated_positions:
                    two_repeated_positions.assign(
                        instance.user, term=sequence['terms'][1])

        if len(sequence['positions']) >= 3:
            if thrice_same_position:
                thrice_same_position.assign(
                    instance.user, term=sequence['terms'][2])


def assign_diffposition_achievements(instance, committee_terms):
    three_unique_positions = get_object_or_none(
        Achievement, short_name='three_unique_positions')
    if len(committee_terms) >= 3:
        # terms is a list of lists
        terms = committee_terms.values()

        if three_unique_positions:
            # find the first semester that this person was on their third
            # different committee
            third_committee_terms = terms[2]
            three_unique_positions.assign(
                instance.user, term=third_committee_terms[0])


def assign_straight_to_the_top_achievement(instance, straight_to_the_top_term):
    straighttothetop = get_object_or_none(
        Achievement, short_name='straighttothetop')
    if straighttothetop:
        straighttothetop.assign(instance.user, term=straight_to_the_top_term)

models.signals.post_save.connect(officership_achievements, sender=Officer)
