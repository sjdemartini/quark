from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.core.urlresolvers import reverse
from django.http import Http404
from django.utils.decorators import method_decorator
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView

from quark.base.models import Term
from quark.project_reports.forms import ProjectReportForm
from quark.project_reports.models import ProjectReport


class ProjectReportCreateView(CreateView):
    form_class = ProjectReportForm
    template_name = 'project_reports/add.html'

    @method_decorator(login_required)
    @method_decorator(
        permission_required('project_reports.add_projectreport',
                            raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(ProjectReportCreateView, self).dispatch(
            *args, **kwargs)

    def get_success_url(self):
        return reverse('project-reports:list-current')


class ProjectReportDeleteView(DeleteView):
    context_object_name = 'project_report'
    model = ProjectReport
    pk_url_kwarg = 'pr_pk'
    template_name = 'project_reports/delete.html'

    @method_decorator(login_required)
    @method_decorator(
        permission_required('project_reports.delete_projectreport',
                            raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(ProjectReportDeleteView, self).dispatch(
            *args, **kwargs)

    def get_success_url(self):
        return reverse('project-reports:list-current')


class ProjectReportDetailView(DetailView):
    context_object_name = 'project_report'
    model = ProjectReport
    pk_url_kwarg = 'pr_pk'
    template_name = 'project_reports/detail.html'


class ProjectReportEditView(UpdateView):
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

    def get_success_url(self):
        return reverse('project-reports:detail',
                       kwargs={'pr_pk': self.object.pk})


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
    model = ProjectReport
    template_name = 'project_reports/list.html'

    def get_context_data(self, **kwargs):
        context = super(ProjectReportListAllView, self).get_context_data(
            **kwargs)
        context['terms'] = Term.objects.all()
        return context
