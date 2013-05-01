from django.contrib import admin

from quark.courses.models import Course
from quark.courses.models import CourseInstance
from quark.courses.models import Department
from quark.courses.models import Instructor


class CourseAdmin(admin.ModelAdmin):
    list_display = ('department', 'number', 'title')
    list_display_links = ('department', 'number')
    list_filter = ('department',)
    search_fields = ('number', 'title', 'department__short_name',
                     'department__long_name', 'department__abbreviation')


class CourseInstanceAdmin(admin.ModelAdmin):
    list_display = ('course', 'term', 'instructor_names')
    list_filter = ('term', 'course')
    search_fields = ('course__number', 'course__department__short_name',
                     'course__title', 'instructors__first_name',
                     'instructors__last_name')

    def instructor_names(self, obj):
        return ', '.join(
            ['{} {}'.format(instructor.first_name, instructor.last_name)
             for instructor in obj.instructors.all()])
    instructor_names.short_description = 'Instructor(s)'


class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('long_name', 'short_name', 'abbreviation')
    list_display_links = ('long_name', 'short_name', 'abbreviation')
    search_fields = ('long_name', 'short_name', 'abbreviation')


class InstructorAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'department')
    list_display_links = ('first_name', 'last_name')
    list_filter = ('department',)
    search_fields = ('first_name', 'last_name')


admin.site.register(Course, CourseAdmin)
admin.site.register(CourseInstance, CourseInstanceAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Instructor, InstructorAdmin)
