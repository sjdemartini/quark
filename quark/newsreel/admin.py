from django.contrib import admin

from quark.newsreel.models import News


class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'blurb', 'rank', 'updated')
    list_display_links = ('title', 'blurb')
    search_fields = ('title', 'blurb')


admin.site.register(News, NewsAdmin)
