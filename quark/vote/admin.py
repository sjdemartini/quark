from django.contrib import admin

from quark.vote.models import Poll
from quark.vote.models import Vote
from quark.vote.models import VoteReceipt


class PollAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_datetime', 'end_datetime',
                    'term', 'creator',)


class VoteAdmin(admin.ModelAdmin):
    list_display = ('poll', 'nominee', 'reason',)


class VoteReceiptAdmin(admin.ModelAdmin):
    list_display = ('poll', 'voter', 'created',)


admin.site.register(Poll, PollAdmin)
admin.site.register(Vote, VoteAdmin)
admin.site.register(VoteReceipt, VoteReceiptAdmin)
