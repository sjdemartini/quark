from django.contrib import admin

from quark.vote.models import Poll


class PollAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_datetime', 'end_datetime',
                    'term', 'creator',)


admin.site.register(Poll, PollAdmin)
