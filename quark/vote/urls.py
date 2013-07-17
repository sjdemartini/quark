from django.conf.urls import patterns
from django.conf.urls import url

from quark.vote.views import PollCreate


urlpatterns = patterns(
    '',
    url(r'^create/$', PollCreate.as_view(), name='create'),
)
