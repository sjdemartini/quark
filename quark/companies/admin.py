from django.contrib import admin

from quark.companies.models import Company
from quark.companies.models import CompanyRep


class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'expiration_date', 'created')
    list_filter = ('expiration_date',)
    search_fields = ('name',)


class CompanyRepAdmin(admin.ModelAdmin):
    list_display = ('user', 'company')
    list_display_links = ('user', 'company')
    list_filter = ('company',)
    search_fields = ('company__name', 'user__first_name', 'user__last_name',
                     'user__username')


admin.site.register(Company, CompanyAdmin)
admin.site.register(CompanyRep, CompanyRepAdmin)
