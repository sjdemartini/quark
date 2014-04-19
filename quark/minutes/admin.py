from django.contrib import admin

from quark.minutes.models import Minutes


class MinutesAdmin(admin.ModelAdmin):
    list_display = ('name', 'meeting_type', 'date', 'term')
    list_filter = ('meeting_type', 'term')
    search_fields = ('name', 'notes')


admin.site.register(Minutes, MinutesAdmin)
