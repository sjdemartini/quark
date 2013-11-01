from django.contrib import admin

from quark.course_surveys.models import Survey


class SurveyAdmin(admin.ModelAdmin):
    list_display = ('course', 'term', 'instructor', 'prof_rating',
                    'course_rating')
    list_display_links = ('course', 'instructor')
    list_filter = ('course', 'term', 'instructor')
    search_fields = ('course__number', 'course__department__short_name',
                     'course__title', 'instructor__first_name',
                     'instructor__last_name')


admin.site.register(Survey, SurveyAdmin)
