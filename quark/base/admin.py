from django.contrib import admin

from quark.base.models import RandomToken


class RandomTokenAdmin(admin.ModelAdmin):
    list_display = ('email', 'season', 'user', 'used', 'created')
    list_filter = ('used', 'created')
    search_fields = ('email',)


admin.site.register(RandomToken, RandomTokenAdmin)
