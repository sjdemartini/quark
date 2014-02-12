from django.conf.urls import patterns
from django.conf.urls import url

from quark.newsreel.views import news_reorder
from quark.newsreel.views import NewsCreateView
from quark.newsreel.views import NewsDeleteView
from quark.newsreel.views import NewsEditView
from quark.newsreel.views import NewsListView


urlpatterns = patterns(
    '',
    url(r'^$', NewsListView.as_view(), name='list'),
    url(r'^add/$', NewsCreateView.as_view(), name='add'),
    url(r'^edit/(?P<news_pk>\d+)/$', NewsEditView.as_view(), name='edit'),
    url(r'^delete/(?P<news_pk>\d+)/$', NewsDeleteView.as_view(), name='delete'),
    url(r'^reorder/$', news_reorder, name='reorder'),
)
