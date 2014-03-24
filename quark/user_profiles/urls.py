from django.conf.urls import patterns
from django.conf.urls import url

from quark.user_profiles.views import UserProfileEditView
from quark.user_profiles.views import UserProfilePictureEditView


urlpatterns = patterns(
    '',
    url(r'^edit/$', UserProfileEditView.as_view(), name='edit'),
    url(r'^picture/$', UserProfilePictureEditView.as_view(), name='edit-pic'),
)
