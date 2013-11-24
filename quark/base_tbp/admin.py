from django.contrib import admin

from quark.base_tbp.models import Officer
from quark.base_tbp.models import OfficerPosition


class OfficerAdmin(admin.ModelAdmin):
    list_display = ('user', 'position', 'term', 'is_chair')
    list_filter = ('term', 'position')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')


admin.site.register(Officer, OfficerAdmin)
admin.site.register(OfficerPosition)
