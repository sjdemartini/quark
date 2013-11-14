from django.conf.urls import patterns
from django.conf.urls import url

from quark.vote.views import PollCreateView
from quark.vote.views import PollListView
from quark.vote.views import ResultsView
from quark.vote.views import VoteCreateView


urlpatterns = patterns(
    '',
    url(r'^$', PollListView.as_view(), name='list'),
    url(r'^create/$', PollCreateView.as_view(), name='create'),
    url(r'^vote/(?P<poll_pk>\d+)/$', VoteCreateView.as_view(), name='vote'),
    url(r'^result/(?P<poll_pk>\d+)/$', ResultsView.as_view(), name='result')
)
