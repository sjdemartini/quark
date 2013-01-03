'''@package quark.helpdesk.admin
Helpdesk admin site registration
'''

from django.contrib import admin

from quark.helpdesk.models import SentMessage

admin.site.register(SentMessage, admin.ModelAdmin)
