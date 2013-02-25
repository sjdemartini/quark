from django.conf.urls import patterns
from django.conf.urls import url

from quark.courses.views import CourseDetailView
from quark.courses.views import CourseListView
from quark.courses.views import DepartmentListView

# pylint: disable=E1120
urlpatterns = patterns(
    '',
    url(r'^(?P<dept_slug>[a-z-]+)/$', CourseListView.as_view(),
        name='view_department_courses'),
    url(r'^(?P<dept_slug>[a-z-]+)/(?P<course_num>[A-Z0-9]+)/$',
        CourseDetailView.as_view(), name='view_course_details'),
    url(r'^$', DepartmentListView.as_view(), name='view_departments')
)
