from django.conf.urls import patterns
from django.conf.urls import url

from quark.emailer.views import CompanyEmailerView
from quark.emailer.views import EventEmailerView
from quark.emailer.views import HelpdeskEmailerView


urlpatterns = patterns(
    '',
    url(r'^helpdesk/$', HelpdeskEmailerView.as_view(),
        name='helpdesk'),
    url(r'^events/(?P<event_pk>\d+)/$', EventEmailerView.as_view(),
        name='event'),
    url(r'^industry/$', CompanyEmailerView.as_view(),
        name='company'),
)
