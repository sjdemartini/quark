from django.contrib import admin

from quark.achievements.models import Achievement
from quark.achievements.models import UserAchievement


class AchievementAdmin(admin.ModelAdmin):
    fields = ('name', 'points', 'privacy', 'manual', 'rank')
    search_fields = ('name', 'points')
    list_filter = ('privacy', 'manual', 'repeatable')
    list_display = ('name', 'points', 'privacy', 'manual',
                    'repeatable', 'rank', 'icon')


class UserAchievementAdmin(admin.ModelAdmin):
    search_fields = (
        'achievement__name', '^user__first_name', '^user__last_name',
        '^user__username')
    list_display = ('achievement', 'user', 'assigner', 'term')

admin.site.register(Achievement, AchievementAdmin)
admin.site.register(UserAchievement, UserAchievementAdmin)
