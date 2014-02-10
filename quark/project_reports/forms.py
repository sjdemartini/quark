from chosen import forms as chosen_forms
from django import forms

from quark.base.fields import VisualDateWidget
from quark.base.forms import ChosenTermMixin
from quark.project_reports.models import ProjectReport
from quark.user_profiles.fields import UserCommonNameChoiceField
from quark.user_profiles.fields import UserCommonNameMultipleChoiceField


class ProjectReportForm(ChosenTermMixin, forms.ModelForm):
    area = chosen_forms.ChosenChoiceField(
        choices=ProjectReport.PROJECT_AREA_CHOICES)
    author = UserCommonNameChoiceField()
    officer_list = UserCommonNameMultipleChoiceField(required=False)
    candidate_list = UserCommonNameMultipleChoiceField(required=False)
    member_list = UserCommonNameMultipleChoiceField(required=False)

    class Meta(object):
        model = ProjectReport
        exclude = ('first_completed_at',)
        widgets = {
            'date': VisualDateWidget(),
            'committee': chosen_forms.ChosenSelect()
        }
