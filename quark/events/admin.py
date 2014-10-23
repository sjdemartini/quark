from django.contrib import admin

from quark.events.models import Event
from quark.events.models import EventAttendance
from quark.events.models import EventSignUp
from quark.events.models import EventType


class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'event_type', 'term')
    list_filter = ('term',)
    search_fields = ('name',)


def get_term(obj):
    return obj.event.term
get_term.short_description = 'Term'


class EventAttendanceAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', get_term)
    list_filter = ('event__term',)
    search_fields = ('event__name', 'user__username',
                     'user__userprofile__preferred_name',
                     'user__first_name', 'user__last_name')


class EventSignupAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'name', 'email', get_term, 'num_guests',
                    'unsignup')
    list_filter = ('event__term',)
    search_fields = ('event__name', 'user__username',
                     'user__userprofile__preferred_name',
                     'user__first_name', 'user__last_name', 'name')


admin.site.register(Event, EventAdmin)
admin.site.register(EventAttendance, EventAttendanceAdmin)
admin.site.register(EventSignUp, EventSignupAdmin)
admin.site.register(EventType)
