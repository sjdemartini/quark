from django.conf.urls import patterns
from django.conf.urls import url

from quark.achievements.views import AchievementDetailView
from quark.achievements.views import LeaderboardListView
from quark.achievements.views import UserAchievementListView


urlpatterns = patterns(
    '',
    url(r'^(?P<achievement_id>\d+)/$',
        AchievementDetailView.as_view(), name='detail'),
    url(r'^leaderboard/$', LeaderboardListView.as_view(), name='leaderboard'),
    url(r'^user/(?P<user_id>\d+)/$',
        UserAchievementListView.as_view(), name='user'),
)
