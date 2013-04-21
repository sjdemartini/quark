from django.contrib import admin

from quark.quote_board.models import Quote


class QuoteAdmin(admin.ModelAdmin):
    list_display = ('quote',)
    search_fields = ['quote']

admin.site.register(Quote, QuoteAdmin)
