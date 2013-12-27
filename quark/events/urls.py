from django.conf.urls import patterns
from django.conf.urls import url

from quark.events.views import EventCreateView
from quark.events.views import EventDetailView
from quark.events.views import EventListView
from quark.events.views import EventSignUpView
from quark.events.views import EventUpdateView
from quark.events.views import IndividualAttendanceListView
from quark.events.views import LeaderboardListView

urlpatterns = patterns(
    '',
    url(r'^$', EventListView.as_view(), name='list'),
    url(r'^add/$', EventCreateView.as_view(), name='add'),
    url(r'^(?P<event_pk>\d+)/$', EventDetailView.as_view(),
        name='detail'),
    url(r'^(?P<event_pk>\d+)/edit/$', EventUpdateView.as_view(), name='edit'),
    url(r'^(?P<event_pk>\d+)/signup/$', EventSignUpView.as_view(),
        name='signup'),
    url(r'^user/(?P<username>[a-zA-Z0-9._-]+)/$',
        IndividualAttendanceListView.as_view(), name='individual-attendance'),
    url(r'^calendar/$', EventListView.as_view(show_all=True,
        template_name='events/calendar.html'), name='calendar'),
    url(r'^leaderboard/$', LeaderboardListView.as_view(), name='leaderboard'),
)
