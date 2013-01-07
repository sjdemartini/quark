from django.contrib import admin

from quark.base.models import RandomToken


class RandomTokenAdmin(admin.ModelAdmin):
    list_display = ('email', 'user', 'used', 'created', 'expiration_date',)
    list_filter = ('used', 'created', 'expiration_date',)
    search_fields = ('email',)


admin.site.register(RandomToken, RandomTokenAdmin)
