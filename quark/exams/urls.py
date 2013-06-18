from django.conf.urls import patterns
from django.conf.urls import url

from quark.exams.views import ExamDeleteView
from quark.exams.views import ExamDownloadView
from quark.exams.views import ExamEditView
from quark.exams.views import ExamFlagCreateView
from quark.exams.views import ExamFlagResolveView
from quark.exams.views import ExamReviewListView
from quark.exams.views import ExamUploadView
from quark.exams.views import PermissionEditView

urlpatterns = patterns(
    '',
    url(r'^upload/$', ExamUploadView.as_view(), name='upload'),
    url(r'^review/$', ExamReviewListView.as_view(), name='review'),
    url(r'^download/(?P<exam_pk>\d+)/$', ExamDownloadView.as_view(),
        name='download'),
    url(r'^edit/(?P<exam_pk>\d+)/$', ExamEditView.as_view(), name='edit'),
    url(r'^delete/(?P<exam_pk>\d+)/$', ExamDeleteView.as_view(), name='delete'),
    url(r'^flag/(?P<exam_pk>\d+)/$', ExamFlagCreateView.as_view(), name='flag'),
    url(r'^resolve/(?P<flag_pk>\d+)/$', ExamFlagResolveView.as_view(),
        name='resolve'),
    url(r'^permission/(?P<permission_pk>\d+)/$', PermissionEditView.as_view(),
        name='permission')
)
