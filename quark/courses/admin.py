from django.contrib import admin

from quark.courses.models import Course
from quark.courses.models import CourseInstance
from quark.courses.models import Department
from quark.courses.models import Instructor


admin.site.register(Course)
admin.site.register(CourseInstance)
admin.site.register(Department)
admin.site.register(Instructor)
