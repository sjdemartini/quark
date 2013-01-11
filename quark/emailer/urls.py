from django.conf.urls import patterns
from django.conf.urls import url

from quark.emailer.views import EventEmailerView
from quark.emailer.views import HelpdeskEmailerView

urlpatterns = patterns(
    '',
    # pylint: disable=E1120
    url(r'^helpdesk/$', HelpdeskEmailerView.as_view(),
        name='helpdesk-index'),
    # pylint: disable=E1120
    url(r'^events/(?P<event_id>\d+)/$', EventEmailerView.as_view(),
        name='event-email-form'),
)
