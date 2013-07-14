from django.contrib import admin

from quark.candidates.models import Candidate
from quark.candidates.models import Challenge
from quark.candidates.models import ChallengeCandidateRequirement
from quark.candidates.models import EventCandidateRequirement
from quark.candidates.models import ExamFileCandidateRequirement
from quark.candidates.models import CandidateRequirementProgress
from quark.candidates.models import ManualCandidateRequirement


class CandidateModelAdmin(admin.ModelAdmin):
    list_display = ('user', 'term', 'initiated')
    list_filter = ('term', 'initiated')
    search_fields = ('user__username', 'user__preferred_name',
                     'user__first_name', 'user__last_name')


class CandidateRequirementAdmin(admin.ModelAdmin):
    exclude = ('requirement_type',)
    list_display = ('credits_needed', 'term')
    list_filter = ('term',)


class CandidateRequirementProgressAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'requirement', 'manually_recorded_credits',
                    'alternate_credits_needed')


class ChallengeAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'challenge_type', 'verifying_user',
                    'verified')
    list_filter = ('challenge_type', 'candidate__term')


class ChallengeCandidateRequirementAdmin(CandidateRequirementAdmin):
    list_display = ('challenge_type', 'credits_needed', 'term')
    list_filter = ('term', 'challenge_type')


class EventCandidateRequirementAdmin(CandidateRequirementAdmin):
    list_display = ('event_type', 'credits_needed', 'term')
    list_filter = ('term', 'event_type')


class ManualCandidateRequirementAdmin(CandidateRequirementAdmin):
    list_display = ('name', 'credits_needed', 'term')


admin.site.register(Candidate, CandidateModelAdmin)
admin.site.register(CandidateRequirementProgress,
                    CandidateRequirementProgressAdmin)
admin.site.register(Challenge, ChallengeAdmin)
admin.site.register(ChallengeCandidateRequirement,
                    ChallengeCandidateRequirementAdmin)
admin.site.register(EventCandidateRequirement,
                    EventCandidateRequirementAdmin)
admin.site.register(ExamFileCandidateRequirement,
                    CandidateRequirementAdmin)
admin.site.register(ManualCandidateRequirement,
                    ManualCandidateRequirementAdmin)
