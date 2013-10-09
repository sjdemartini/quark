from django.contrib import admin

from quark.user_profiles.models import CollegeStudentInfo
from quark.user_profiles.models import StudentOrgUserProfile
from quark.user_profiles.models import UserContactInfo


class CollegeStudentInfoAdmin(admin.ModelAdmin):
    list_display = ('user', 'major', 'start_term', 'grad_term')
    list_filter = ('major', 'start_term', 'grad_term')
    search_fields = ('user__username', 'user__first_name', 'user__last_name',
                     'major')


class StudentOrgUserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'initiation_term')
    list_filter = ('initiation_term',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name')


class UserContactInfoAdmin(admin.ModelAdmin):
    list_display = ('user', 'alt_email', 'cell_phone', 'receive_text')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')


admin.site.register(CollegeStudentInfo, CollegeStudentInfoAdmin)
admin.site.register(StudentOrgUserProfile, StudentOrgUserProfileAdmin)
admin.site.register(UserContactInfo, UserContactInfoAdmin)
