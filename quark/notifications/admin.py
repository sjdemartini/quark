from django.contrib import admin

from quark.notifications.models import Notification


class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'title', 'cleared')
    list_filter = ('status', 'cleared', 'content_type')
    search_fields = ('user__username', 'user__first_name', 'user__last_name',
                     'title', 'subtitle', 'description')


admin.site.register(Notification, NotificationAdmin)
