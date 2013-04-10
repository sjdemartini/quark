from django.conf.urls import patterns
from django.conf.urls import url

from quark.courses.views import CourseDetailView
from quark.courses.views import CourseListView
from quark.courses.views import DepartmentListView
from quark.courses.views import InstructorDetailView

# pylint: disable=E1120
urlpatterns = patterns(
    '',
    url(r'^instructors/(?P<inst_pk>[0-9]+)/$',
        InstructorDetailView.as_view(), name='instructor'),
    url(r'^(?P<dept_slug>[A-Za-z-]+)/$', CourseListView.as_view(),
        name='department-courses'),
    url(r'^(?P<dept_slug>[A-Za-z-]+)/(?P<course_num>[A-Za-z0-9]+)/$',
        CourseDetailView.as_view(), name='detail'),
    url(r'^$', DepartmentListView.as_view(), name='list-departments')
)
