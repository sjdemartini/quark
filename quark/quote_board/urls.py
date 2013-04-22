from django.conf.urls import patterns
from django.conf.urls import url

from quark.quote_board.views import QuoteCreateView
from quark.quote_board.views import QuoteDetailView
from quark.quote_board.views import QuoteListView


# pylint: disable=E1120
urlpatterns = patterns(
    '',
    url(r'^$', QuoteListView.as_view(), name='list'),
    url(r'^add/$', QuoteCreateView.as_view(), name='add'),
    url(r'^view/(?P<quote_id>\d+)/$', QuoteDetailView.as_view(), name='detail'),
)
