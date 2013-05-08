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
    list_display = ('event', 'person', get_term)
    list_filter = ('event__term',)
    search_fields = ('event__name', 'person__username',
                     'person__preferred_name', 'person__first_name',
                     'person__last_name')


class EventSignupAdmin(admin.ModelAdmin):
    list_display = ('event', 'person', 'name', get_term, 'num_guests',
                    'unsignup')
    list_filter = ('event__term',)
    search_fields = ('event__name', 'person__username',
                     'person__preferred_name', 'person__first_name',
                     'person__last_name', 'name')


admin.site.register(Event, EventAdmin)
admin.site.register(EventAttendance, EventAttendanceAdmin)
admin.site.register(EventSignUp, EventSignupAdmin)
admin.site.register(EventType)
