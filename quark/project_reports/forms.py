from django import forms
from django.contrib.admin import widgets

from quark.project_reports.models import ProjectReport


class ProjectReportForm(forms.ModelForm):
    # TODO(giovanni): Implement Chosen plugin in an __init__ method to be used
    #                 for certain form fields: author; officer_list;
    #                 candidate_list; member_list; semester; committee; area

    date = forms.DateField(widget=widgets.AdminDateWidget)
    # TODO(giovanni): Add fields similar to noiro_main.fields for the fields:
    #                 author; officer_list; candiate_list; member_list

    class Meta:
        model = ProjectReport
        exclude = ('first_completed_at',)
