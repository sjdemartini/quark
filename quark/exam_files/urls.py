from django.conf.urls import patterns
from django.conf.urls import url

from quark.exam_files.views import ExamDeleteView
from quark.exam_files.views import ExamEditView
from quark.exam_files.views import ExamFlagCreateView
from quark.exam_files.views import ExamFlagResolveView
from quark.exam_files.views import ExamListView
from quark.exam_files.views import ExamReviewListView
from quark.exam_files.views import ExamUploadView

urlpatterns = patterns(
    '',
    url(r'^(?P<short_name>[A-Za-z]+)/(?P<number>[A-Za-z0-9]+)/$',
        ExamListView.as_view(), name='list'),
    url(r'^upload/$', ExamUploadView.as_view(), name='upload'),
    url(r'^review/$', ExamReviewListView.as_view(), name='review'),
    url(r'^edit/(?P<exam_id>\d+)/$', ExamEditView.as_view(), name='edit'),
    url(r'^delete/(?P<exam_id>\d+)/$', ExamDeleteView.as_view(), name='delete'),
    url(r'^flag/(?P<exam_id>\d+)/$', ExamFlagCreateView.as_view(), name='flag'),
    url(r'^resolve/(?P<exam_id>\d+)/$', ExamFlagResolveView.as_view(),
        name='resolve')
)
