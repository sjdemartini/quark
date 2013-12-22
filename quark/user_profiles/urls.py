from django.conf.urls import patterns
from django.conf.urls import url

from quark.user_profiles.views import UserProfileEditView


urlpatterns = patterns(
    '',
    url(r'^edit/$', UserProfileEditView.as_view(), name='edit'),
)
