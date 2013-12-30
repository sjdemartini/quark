from django.contrib import admin

from quark.candidates.models import Candidate
from quark.candidates.models import Challenge
from quark.candidates.models import ChallengeType
from quark.candidates.models import ChallengeCandidateRequirement
from quark.candidates.models import EventCandidateRequirement
from quark.candidates.models import ExamFileCandidateRequirement
from quark.candidates.models import CandidateRequirementProgress
from quark.candidates.models import ManualCandidateRequirement


class CandidateModelAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_name', 'term', 'initiated')
    list_filter = ('term', 'initiated')
    search_fields = ('user__username', 'user__userprofile__preferred_name',
                     'user__first_name', 'user__last_name')

    def user_name(self, obj):
        return obj.user.userprofile.get_common_name()
    user_name.short_description = 'Name'


class CandidateRequirementAdmin(admin.ModelAdmin):
    exclude = ('requirement_type',)
    list_display = ('credits_needed', 'term')
    list_filter = ('term',)


class CandidateRequirementProgressAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'requirement', 'manually_recorded_credits',
                    'alternate_credits_needed')
    search_fields = ('candidate__user__username',
                     'candidate__user__userprofile__preferred_name',
                     'candidate__user__first_name',
                     'candidate__user__last_name')


class ChallengeAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'challenge_type', 'verifying_user',
                    'verified')
    list_filter = ('challenge_type', 'candidate__term')
    search_fields = ('candidate__user__username',
                     'candidate__user__userprofile__preferred_name',
                     'candidate__user__first_name',
                     'candidate__user__last_name')


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
admin.site.register(ChallengeType)
