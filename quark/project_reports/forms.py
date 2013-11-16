from chosen import forms as chosen_forms
from django import forms
from django.contrib.auth import get_user_model

from quark.base.fields import VisualDateField
from quark.base.forms import ChosenTermMixin
from quark.base_tbp.models import OfficerPosition
from quark.project_reports.models import ProjectReport
from quark.user_profiles.fields import UserCommonNameChoiceField
from quark.user_profiles.fields import UserCommonNameMultipleChoiceField


class ProjectReportForm(ChosenTermMixin, forms.ModelForm):
    committee = chosen_forms.ChosenModelChoiceField(
        queryset=OfficerPosition.objects.filter(
            position_type=OfficerPosition.TBP_OFFICER))
    area = chosen_forms.ChosenChoiceField(
        choices=ProjectReport.PROJECT_AREA_CHOICES)
    author = UserCommonNameChoiceField(
        queryset=get_user_model().objects.all())
    officer_list = UserCommonNameMultipleChoiceField(
        queryset=get_user_model().objects.all(), required=False)
    candidate_list = UserCommonNameMultipleChoiceField(
        queryset=get_user_model().objects.all(), required=False)
    member_list = UserCommonNameMultipleChoiceField(
        queryset=get_user_model().objects.all(), required=False)
    date = VisualDateField(label='Date (YYYY-MM-DD)')

    class Meta(object):
        model = ProjectReport
        exclude = ('first_completed_at',)
