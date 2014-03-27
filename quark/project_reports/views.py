from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.core.urlresolvers import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView

from quark.base.models import Term
from quark.base.views import TermParameterMixin
from quark.project_reports.forms import ProjectReportForm
from quark.project_reports.models import ProjectReport


class ProjectReportCreateView(CreateView):
    form_class = ProjectReportForm
    success_url = reverse_lazy('project_reports:list')
    template_name = 'project_reports/add.html'

    @method_decorator(login_required)
    @method_decorator(
        permission_required('project_reports.add_projectreport',
                            raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(ProjectReportCreateView, self).dispatch(
            *args, **kwargs)

    def get_initial(self):
        current_term = Term.objects.get_current_term()
        return {'author': self.request.user,  # usable since login_required
                'term': current_term.id if current_term else None}


class ProjectReportDeleteView(DeleteView):
    context_object_name = 'project_report'
    model = ProjectReport
    pk_url_kwarg = 'pr_pk'
    success_url = reverse_lazy('project_reports:list')
    template_name = 'project_reports/delete.html'

    @method_decorator(login_required)
    @method_decorator(
        permission_required('project_reports.delete_projectreport',
                            raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(ProjectReportDeleteView, self).dispatch(
            *args, **kwargs)


class ProjectReportDetailView(DetailView):
    context_object_name = 'project_report'
    model = ProjectReport
    pk_url_kwarg = 'pr_pk'
    template_name = 'project_reports/detail.html'

    @method_decorator(login_required)
    @method_decorator(
        permission_required('project_reports.view_project_reports',
                            raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(ProjectReportDetailView, self).dispatch(
            *args, **kwargs)


class ProjectReportEditView(UpdateView):
    context_object_name = 'project_report'
    form_class = ProjectReportForm
    model = ProjectReport
    pk_url_kwarg = 'pr_pk'
    template_name = 'project_reports/edit.html'

    @method_decorator(login_required)
    @method_decorator(
        permission_required('project_reports.change_projectreport',
                            raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(ProjectReportEditView, self).dispatch(
            *args, **kwargs)


class ProjectReportListView(TermParameterMixin, ListView):
    """View for showing all project reports from a given term.

    Term is specified via URL parameter, using the TermParameterMixin.
    """
    context_object_name = 'project_reports'
    template_name = 'project_reports/list.html'

    @method_decorator(login_required)
    @method_decorator(
        permission_required('project_reports.view_project_reports',
                            raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(ProjectReportListView, self).dispatch(
            *args, **kwargs)

    def get_queryset(self):
        return ProjectReport.objects.filter(term=self.display_term)


class ProjectReportListAllView(ListView):
    """View for showing all project reports from all terms."""
    context_object_name = 'project_reports'
    model = ProjectReport
    template_name = 'project_reports/list.html'

    @method_decorator(login_required)
    @method_decorator(
        permission_required('project_reports.view_project_reports',
                            raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(ProjectReportListAllView, self).dispatch(
            *args, **kwargs)
