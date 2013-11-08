from django.conf.urls import patterns
from django.conf.urls import url

from quark.project_reports.views import ProjectReportCreateView
from quark.project_reports.views import ProjectReportDeleteView
from quark.project_reports.views import ProjectReportDetailView
from quark.project_reports.views import ProjectReportEditView
from quark.project_reports.views import ProjectReportListAllView
from quark.project_reports.views import ProjectReportListView


urlpatterns = patterns(
    '',
    url(r'^$', ProjectReportListView.as_view(), name='list'),
    url(r'^(?P<pr_pk>\d+)/$', ProjectReportDetailView.as_view(),
        name='detail'),
    url(r'^(?P<pr_pk>\d+)/edit/$', ProjectReportEditView.as_view(),
        name='edit'),
    url(r'^(?P<pr_pk>\d+)/delete/$', ProjectReportDeleteView.as_view(),
        name='delete'),
    url(r'^add/$', ProjectReportCreateView.as_view(), name='add'),
    url(r'^all/$', ProjectReportListAllView.as_view(), name='list-all'),
)
