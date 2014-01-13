from django.conf.urls import patterns
from django.conf.urls import url

from quark.newsreel.views import news_reorder
from quark.newsreel.views import NewsListView


urlpatterns = patterns(
    '',
    url(r'^$', NewsListView.as_view(), name='list'),
    url(r'^reorder/$', news_reorder, name='reorder'),
)
