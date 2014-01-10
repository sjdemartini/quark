from django.conf.urls import patterns
from django.conf.urls import url

from quark.courses.views import CourseDetailView
from quark.courses.views import CourseListView
from quark.courses.views import CourseDepartmentListView
from quark.courses.views import InstructorCreateView
from quark.courses.views import InstructorDepartmentListView
from quark.courses.views import InstructorDeleteView
from quark.courses.views import InstructorDetailView
from quark.courses.views import InstructorEditView
from quark.courses.views import InstructorListView


urlpatterns = patterns(
    '',
    url(r'^$', CourseDepartmentListView.as_view(),
        name='course-department-list'),
    url(r'^(?P<dept_slug>(?!instructors)[A-Za-z-]+)/$',
        CourseListView.as_view(), name='course-list'),
    url(r'^(?P<dept_slug>(?!instructors)[A-Za-z-]+)/'
        '(?P<course_num>[A-Za-z0-9]+)/$',
        CourseDetailView.as_view(), name='course-detail'),
    url(r'^instructors/$', InstructorDepartmentListView.as_view(),
        name='instructor-department-list'),
    url(r'^instructors/add/$', InstructorCreateView.as_view(),
        name='add-instructor'),
    url(r'^instructors/(?P<dept_slug>[A-Za-z-]+)/$',
        InstructorListView.as_view(), name='instructor-list'),
    url(r'^instructors/(?P<inst_pk>[0-9]+)/$',
        InstructorDetailView.as_view(), name='instructor-detail'),
    url(r'^instructors/(?P<inst_pk>[0-9]+)/edit/$',
        InstructorEditView.as_view(), name='edit-instructor'),
    url(r'^instructors/(?P<inst_pk>[0-9]+)/delete/$',
        InstructorDeleteView.as_view(), name='delete-instructor'),
)
