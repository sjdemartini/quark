from django.conf.urls import patterns
from django.conf.urls import url

from quark.resumes.views import ResumeDownloadView
from quark.resumes.views import ResumeEditView


urlpatterns = patterns(
    '',
    url(r'^$', ResumeEditView.as_view(), name='edit'),
    url(r'^download/$', ResumeDownloadView.as_view(), name='download'),
)
