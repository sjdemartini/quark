from django.conf.urls import patterns
from django.conf.urls import url

from quark.exams.views import ExamDeleteView
from quark.exams.views import ExamEditView
from quark.exams.views import ExamFlagCreateView
from quark.exams.views import ExamFlagResolveView
from quark.exams.views import ExamReviewListView
from quark.exams.views import ExamUploadView

urlpatterns = patterns(
    '',
    url(r'^upload/$', ExamUploadView.as_view(), name='upload'),
    url(r'^review/$', ExamReviewListView.as_view(), name='review'),
    url(r'^edit/(?P<exam_id>\d+)/$', ExamEditView.as_view(), name='edit'),
    url(r'^delete/(?P<exam_id>\d+)/$', ExamDeleteView.as_view(), name='delete'),
    url(r'^flag/(?P<exam_id>\d+)/$', ExamFlagCreateView.as_view(), name='flag'),
    url(r'^resolve/(?P<exam_id>\d+)/$', ExamFlagResolveView.as_view(),
        name='resolve')
)
