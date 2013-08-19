from chosen import forms as chosen_forms
from django import forms
from django.contrib.auth import get_user_model

from quark.base.models import Term
from quark.base_tbp.models import OfficerPosition
from quark.project_reports.models import ProjectReport
from quark.user_profiles.fields import UserCommonNameChoiceField
from quark.user_profiles.fields import UserCommonNameMultipleChoiceField


class ProjectReportForm(forms.ModelForm):
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
    #TODO(giovanni): use a visual date widget
    date = forms.DateField(label='Date (YYYY-MM-DD)')

    class Meta(object):
        model = ProjectReport
        exclude = ('first_completed_at',)

    def __init__(self, *args, **kwargs):
        super(ProjectReportForm, self).__init__(*args, **kwargs)
        # For fields which reference a QuerySet that must be evaluated (i.e,
        # hits the database and isn't "lazy"), create fields in the __init__ to
        # avoid database errors in Django's test runner
        self.fields['term'] = chosen_forms.ChosenModelChoiceField(
            queryset=Term.objects.get_terms(
                include_future=False, include_summer=True, reverse=False))
