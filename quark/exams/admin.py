from django.contrib import admin

from quark.exams.models import Exam
from quark.exams.models import ExamFlag
from quark.exams.models import InstructorPermission


class ExamAdmin(admin.ModelAdmin):
    list_display = ('course_instance', 'exam_number', 'exam_type',
                    'instructor_names', 'verified', 'flags',
                    'blacklisted')
    list_filter = ('verified', 'flags', 'blacklisted')
    search_fields = ('course_instance__course__number',
                     'course_instance__course__department__short_name',
                     'course_instance__course__title',
                     'course_instance__instructors__first_name',
                     'course_instance__instructors__last_name')

    def instructor_names(self, obj):
        return ', '.join(
            ['{} {}'.format(instructor.first_name, instructor.last_name)
             for instructor in obj.instructors])
    instructor_names.short_description = 'Instructor(s)'


class ExamFlagAdmin(admin.ModelAdmin):
    list_display = ('exam', 'created', 'resolved')
    list_filter = ('resolved',)
    search_fields = ('exam__course_instance__course__number',
                     'exam__course_instance__department__short_name')


class InstructorPermissionAdmin(admin.ModelAdmin):
    list_display = ('instructor', 'permission_allowed')
    list_filter = ('permission_allowed', 'instructor__department')
    search_fields = ('instructor__first_name', 'instructor__last_name')


admin.site.register(Exam, ExamAdmin)
admin.site.register(ExamFlag, ExamFlagAdmin)
admin.site.register(InstructorPermission, InstructorPermissionAdmin)
