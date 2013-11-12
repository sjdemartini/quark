from django.contrib.auth import get_user_model
from django.core.files import File

from quark.base.models import Term
from quark.base_tbp.models import OfficerPosition
from quark.project_reports.models import ProjectReport

from scripts import get_json_data
from scripts import NOIRO_MEDIA_LOCATION
from scripts.import_base_models import SEMESTER_TO_TERM


user_model = get_user_model()


def import_project_reports():
    models = get_json_data('projects.projectreport.json')
    for model in models:
        fields = model['fields']

        term = Term.objects.get(pk=SEMESTER_TO_TERM[fields['semester']])
        project_report, _ = ProjectReport.objects.get_or_create(
            pk=model['pk'],
            term=term,
            date=fields['date'],
            title=fields['title'],
            author=user_model.objects.get(pk=fields['author']),
            committee=OfficerPosition.objects.get(pk=fields['committee']),
            area=fields['area'],
            organize_hours=fields['organize_hours'],
            participate_hours=fields['participate_hours'],
            is_new=fields['is_new'],
            other_group=fields['other_group'],
            description=fields['description'],
            purpose=fields['purpose'],
            organization=fields['organization'],
            cost=fields['cost'],
            problems=fields['problems'],
            results=fields['results'],
            non_tbp=fields['non_tbp'],
            complete=fields['complete'])
        for officer_pk in fields['officer_list']:
            project_report.officer_list.add(user_model.objects.get(
                pk=officer_pk))
        for member_pk in fields['member_list']:
            project_report.member_list.add(user_model.objects.get(
                pk=member_pk))
        for candidate_pk in fields['candidate_list']:
            project_report.candidate_list.add(user_model.objects.get(
                pk=candidate_pk))
        if fields['attachment']:
            with open(NOIRO_MEDIA_LOCATION +
                      fields['attachment'], 'r') as attachment:
                project_report.attachment = File(attachment)
                project_report.save()
