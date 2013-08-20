from chosen import forms as chosen_forms
from django import forms
from django.contrib.admin import widgets
from django.contrib.auth import get_user_model

from quark.accounts.fields import UserCommonNameChoiceField
from quark.accounts.fields import UserCommonNameMultipleChoiceField
from quark.base.models import Term
from quark.base_tbp.models import OfficerPosition
from quark.project_reports.models import ProjectReport


class ProjectReportForm(forms.ModelForm):
    committtee = chosen_forms.ChosenModelChoiceField(
        queryset=OfficerPosition.objects.filter(
            position_type=OfficerPosition.TBP_OFFICER))
    area = chosen_forms.ChosenChoiceField()
    author = UserCommonNameChoiceField(
        queryset=get_user_model().objects.all())
    officer_list = UserCommonNameMultipleChoiceField(
        queryset=get_user_model().objects.all(), required=False)
    candidate_list = UserCommonNameMultipleChoiceField(
        queryset=get_user_model().objects.all(), required=False)
    member_list = UserCommonNameMultipleChoiceField(
        queryset=get_user_model().objects.all(), required=False)
    date = forms.DateField(widget=widgets.AdminDateWidget)

    class Meta(object):
        model = ProjectReport
        exclude = ('first_completed_at',)
        widges = {
            'term': chosen_forms.ChosenSelect(),
        }

    def __init__(self, *args, **kwargs):
        super(ProjectReportForm, self).__init__(*args, **kwargs)
        # For fields which reference a QuerySet that must be evaluated (i.e,
        # hits the database and isn't "lazy"), create fields in the __init__ to
        # avoid database errors in Django's test runner
        self.fields['term'].queryset = Term.objects.get_terms(
            include_future=False, include_summer=True, reverse=False)
