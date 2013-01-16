from django.http import Http404
from django.views.generic import ListView

from quark.base.models import Term
from quark.project_reports.models import ProjectReport


class ProjectReportListView(ListView):
    context_object_name = 'project_reports'
    template_name = 'project_reports/list.html'
    display_term = None

    def dispatch(self, *args, **kwargs):
        term = kwargs.get('term', '')
        if not term:
            self.display_term = Term.objects.get_current_term()
        else:
            self.display_term = Term.objects.get_by_url_name(term)
            if self.display_term is None:
                raise Http404
        return super(ProjectReportListView, self).dispatch(
            *args, **kwargs)

    def get_queryset(self):
        return ProjectReport.objects.filter(term=self.display_term)

    def get_context_data(self, **kwargs):
        context = super(ProjectReportListView, self).get_context_data(
            **kwargs)
        context['terms'] = Term.objects.all()
        context['display_term'] = self.display_term
        return context


class ProjectReportListAllView(ListView):
    context_object_name = 'project_reports'
    template_name = 'project_reports/list.html'
    queryset = ProjectReport.objects.all()

    def get_context_data(self, **kwargs):
        context = super(ProjectReportListAllView, self).get_context_data(
            **kwargs)
        context['terms'] = Term.objects.all()
        return context
