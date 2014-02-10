from django.conf.urls import patterns
from django.conf.urls import url

from quark.notifications.views import clear_notification


urlpatterns = patterns(
    '',
    url(r'^clear/(?P<notification_pk>\d+)/$', clear_notification, name='clear'),
)
