from django.contrib import admin

from quark.base_tbp.models import Officer
from quark.base_tbp.models import OfficerPosition


admin.site.register(Officer)
admin.site.register(OfficerPosition)
