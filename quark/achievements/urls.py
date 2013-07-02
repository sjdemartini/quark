from django.conf.urls import patterns
from django.conf.urls import url

from quark.achievements.views import LeaderboardListView


urlpatterns = patterns(
    '',
    url(r'^leaderboard/$', LeaderboardListView.as_view(), name='leaderboard'),
)
