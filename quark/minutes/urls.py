from django.conf.urls import patterns
from django.conf.urls import url

from quark.minutes.views import MinutesListView
from quark.minutes.views import MinutesCreateView
from quark.minutes.views import MinutesDetailView
from quark.minutes.views import MinutesEditView
from quark.minutes.views import MinutesUploadView

# pylint: disable=E1120
urlpatterns = patterns(
    '',
    url(r'^$', MinutesListView.as_view(),
        name='index'),
    url(r'^(?P<minutes_id>\d+)/$', MinutesDetailView.as_view(),
        name='detail'),
    url(r'^edit/(?P<minutes_id>\d+)/$', MinutesEditView.as_view(),
        name='edit'),
    url(r'^add/$', MinutesCreateView.as_view(),
        name='add'),
    url(r'^upload/$', MinutesUploadView.as_view(),
        name='upload')
)
