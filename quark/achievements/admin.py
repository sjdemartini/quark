from django.contrib import admin

from quark.achievements.models import Achievement
from quark.achievements.models import UserAchievement


class AchievementAdmin(admin.ModelAdmin):
    fields = (
        'name', 'description', 'points', 'goal', 'privacy', 'manual', 'rank',
        'acquired_icon', 'unacquired_icon', 'icon_creator', 'sequence',
        'category')
    search_fields = ('name', 'points')
    list_filter = ('privacy', 'manual', 'repeatable')
    list_display = ('name', 'points', 'goal', 'privacy', 'manual', 'rank')


class UserAchievementAdmin(admin.ModelAdmin):
    search_fields = (
        'achievement__name', '^user__first_name', '^user__last_name',
        '^user__username')
    list_display = ('achievement', 'user', 'acquired', 'progress',
                    'assigner', 'term')

admin.site.register(Achievement, AchievementAdmin)
admin.site.register(UserAchievement, UserAchievementAdmin)
