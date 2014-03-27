import os

from django.contrib.auth import get_user_model
from django.core.files import File

from quark.base.models import Officer
from quark.base.models import Term
from quark.candidates.models import Candidate
from quark.candidates.models import CandidateRequirementProgress
from quark.candidates.models import ChallengeCandidateRequirement
from quark.candidates.models import Challenge
from quark.candidates.models import ChallengeType
from quark.candidates.models import EventCandidateRequirement
from quark.candidates.models import ExamFileCandidateRequirement
from quark.events.models import EventType
from scripts import get_json_data
from scripts import NOIRO_MEDIA_LOCATION
from scripts.import_base_models import SEMESTER_TO_TERM
from scripts.import_user_models import HAS_INITIATED


CANDIDATE_PHOTO_LOCATION = 'candpics'
# Because all candidate requirement models are a subclass of
# CandidateRequirement, whenever a candidate requirement is created, a
# CandidateRequirement is created as well with the same pk. Thus, candidate
# requirements of different types cannot share the same pk even though they are
# different models, and the pk's for event requirements need to be shifted by 16
# (the number of challenge requirements, which are imported first).
EVENT_REQUIREMENT_PK_CONVERSION = 16

user_model = get_user_model()


def import_candidates():
    models = get_json_data('candidate_portal.candidateprofile.json')
    for model in models:
        fields = model['fields']
        term = Term.objects.get(pk=SEMESTER_TO_TERM[fields['semester']])

        user_pk = fields['user']
        candidate, _ = Candidate.objects.get_or_create(
            pk=model['pk'],
            user=user_model.objects.get(pk=user_pk),
            term=term,
            initiated=HAS_INITIATED[user_pk])

        photo_location = os.path.join(
            NOIRO_MEDIA_LOCATION,
            CANDIDATE_PHOTO_LOCATION,
            term.get_url_name(),
            str(fields['user']) + '.jpg')
        if os.path.exists(photo_location):
            with open(photo_location, 'r') as photo:
                candidate.photo = File(photo)
                candidate.save()


def import_challenge_requirements():
    models = get_json_data('candidate_portal.challengerequirement.json')
    for model in models:
        fields = model['fields']

        challenge_type, _ = ChallengeType.objects.get_or_create(
            name=fields['challenge_type'])

        ChallengeCandidateRequirement.objects.get_or_create(
            pk=model['pk'],
            credits_needed=fields['num_required'],
            term=Term.objects.get(pk=SEMESTER_TO_TERM[fields['semester']]),
            challenge_type=challenge_type)


def import_challenges():
    models = get_json_data('candidate_portal.challenge.json')
    for model in models:
        fields = model['fields']
        Challenge.objects.get_or_create(
            pk=model['pk'],
            candidate=Candidate.objects.get(pk=fields['candidate_profile']),
            challenge_type=ChallengeCandidateRequirement.objects.get(
                pk=fields['challenge_type']).challenge_type,
            description=fields['description'],
            verifying_user=Officer.objects.get(pk=fields['officer']).user,
            verified=fields['verified'])


def import_event_requirements():
    models = get_json_data('candidate_portal.eventrequirement.json')
    for model in models:
        fields = model['fields']
        new_pk = model['pk'] + EVENT_REQUIREMENT_PK_CONVERSION
        EventCandidateRequirement.objects.get_or_create(
            pk=new_pk,
            credits_needed=fields['num_required'],
            term=Term.objects.get(pk=SEMESTER_TO_TERM[fields['semester']]),
            event_type=EventType.objects.get(pk=fields['event_type']))


def import_candidate_progresses():
    models = get_json_data('candidate_portal.eventrequirementexception.json')
    for model in models:
        fields = model['fields']
        new_pk = fields['event_requirement'] + EVENT_REQUIREMENT_PK_CONVERSION
        CandidateRequirementProgress.objects.get_or_create(
            pk=model['pk'],
            candidate=Candidate.objects.get(pk=fields['candidate_profile']),
            requirement=EventCandidateRequirement.objects.get(pk=new_pk),
            alternate_credits_needed=fields['new_num_required'],
            comments=fields['comments'])


def import_exam_files_requirements():
    # Only create exam file requirements for non-summer terms between 2009 and
    # 2013 inclusive (when noiro was being used)
    terms = Term.objects.get_terms(
        include_summer=False).filter(year__gte=2009).filter(year__lte=2013)
    for term in terms:
        ExamFileCandidateRequirement.objects.get_or_create(
            credits_needed=2, term=term)
