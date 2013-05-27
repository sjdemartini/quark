from django.conf.urls import patterns
from django.conf.urls import url

from quark.emailer.views import EventEmailerView
from quark.emailer.views import HelpdeskEmailerView
from quark.emailer.views import CompanyEmailerView


urlpatterns = patterns(
    '',
    url(r'^helpdesk/$', HelpdeskEmailerView.as_view(),
        name='helpdesk'),
    url(r'^events/(?P<event_id>\d+)/$', EventEmailerView.as_view(),
        name='event'),
    url(r'^indrel/$', CompanyEmailerView.as_view(),
        name='company'),
)
