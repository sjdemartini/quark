from django.contrib import admin

from quark.user_profiles.models import CollegeStudentInfo
from quark.user_profiles.models import StudentOrgUserProfile
from quark.user_profiles.models import UserProfile


class CollegeStudentInfoAdmin(admin.ModelAdmin):
    list_display = ('user', 'start_term', 'grad_term')
    list_filter = ('major', 'start_term', 'grad_term')
    search_fields = ('user__username', 'user__first_name', 'user__last_name',
                     'major__long_name', 'major__short_name')


class StudentOrgUserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'initiation_term')
    list_filter = ('initiation_term',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name')


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'preferred_name', 'last_name', 'alt_email',
                    'cell_phone', 'receive_text')
    search_fields = ('user__username', 'user__first_name', 'user__last_name',
                     'preferred_name')

    def last_name(self, obj):
        return obj.user.last_name


admin.site.register(CollegeStudentInfo, CollegeStudentInfoAdmin)
admin.site.register(StudentOrgUserProfile, StudentOrgUserProfileAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
