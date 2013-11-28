from django.contrib import admin

from quark.base.models import Major
from quark.base.models import Term
from quark.base.models import University


class MajorAdmin(admin.ModelAdmin):
    list_display = ('short_name', 'long_name', 'university')
    list_display_links = ('short_name', 'long_name')
    list_filter = ('university',)
    search_fields = ('short_name', 'long_name', 'university__short_name',
                     'university__long_name')


class TermAdmin(admin.ModelAdmin):
    exclude = ('id',)


class UniversityAdmin(admin.ModelAdmin):
    list_display = ('short_name', 'long_name')
    list_display_links = ('short_name', 'long_name')
    search_fields = ('short_name', 'long_name')


admin.site.register(Major, MajorAdmin)
admin.site.register(Term, TermAdmin)
admin.site.register(University, UniversityAdmin)
