from django.contrib import admin

from quark.base.models import Major
from quark.base.models import RandomToken
from quark.base.models import Term
from quark.base.models import University


class RandomTokenAdmin(admin.ModelAdmin):
    list_display = ('email', 'user', 'used', 'created', 'expiration_date',)
    list_filter = ('used', 'created', 'expiration_date',)
    search_fields = ('email',)


admin.site.register(Major)
admin.site.register(RandomToken, RandomTokenAdmin)
admin.site.register(Term)
admin.site.register(University)
