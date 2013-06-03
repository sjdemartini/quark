from django.conf.urls import patterns
from django.conf.urls import url

from quark.past_presidents.views import PastPresidentsListView
from quark.past_presidents.views import PastPresidentsDetailView

urlpatterns = patterns(
    '',
    url(r'^$', PastPresidentsListView.as_view(), name='list'),
    url(r'^words/(?P<past_president_id>\d+)/$',
        PastPresidentsDetailView.as_view(), name='detail'),
)
