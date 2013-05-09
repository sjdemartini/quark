from chosen import forms as chosen_forms
from django import forms
from django.contrib.admin import widgets

from quark.auth.models import User
from quark.auth.fields import UserCommonNameChoiceField
# TODO(giovanni): figure out standard for importing, example:
#                 chosen_forms.ChosenChoiceField or just ChosenChoiceField
from quark.auth.fields import UserCommonNameMultipleChoiceField
from quark.base.models import Term
from quark.base_tbp.models import OfficerPosition
from quark.project_reports.models import ProjectReport


class ProjectReportForm(forms.ModelForm):
    committtee = chosen_forms.ChosenModelChoiceField(
        queryset=OfficerPosition.objects.filter(
            position_type=OfficerPosition.TBP_OFFICER))
    area = chosen_forms.ChosenChoiceField()
    author = UserCommonNameChoiceField(queryset=User.objects.all())
    officer_list = UserCommonNameMultipleChoiceField(
        queryset=User.objects.all(), required=False)
    candidate_list = UserCommonNameMultipleChoiceField(
        queryset=User.objects.all(), required=False)
    member_list = UserCommonNameMultipleChoiceField(
        queryset=User.objects.all(), required=False)
    date = forms.DateField(widget=widgets.AdminDateWidget)

    class Meta:
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
