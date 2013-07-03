from django.contrib.auth.decorators import login_required
from django.core.servers.basehttp import FileWrapper
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.encoding import smart_bytes
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView

from quark.accounts.decorators import officer_required
from quark.exams.forms import EditForm
from quark.exams.forms import EditPermissionForm
from quark.exams.forms import FlagForm
from quark.exams.forms import ResolveFlagForm
from quark.exams.forms import UploadForm
from quark.exams.models import Exam
from quark.exams.models import ExamFlag
from quark.exams.models import InstructorPermission


class ExamUploadView(CreateView):
    form_class = UploadForm
    template_name = 'exams/upload.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ExamUploadView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        """Assign submitter to the exam, and convert the exam_file to pdf
        if it is not already a pdf.
        """
        exam = form.save(commit=False)
        exam.submitter = self.request.user
        exam.save()
        return super(ExamUploadView, self).form_valid(form)

    def get_success_url(self):
        return reverse('courses:list-departments')


class ExamDownloadView(DetailView):
    """View for downloading exams."""
    exam = None

    def dispatch(self, *args, **kwargs):
        self.exam = get_object_or_404(Exam, pk=self.kwargs['exam_pk'])
        return super(ExamDownloadView, self).dispatch(*args, **kwargs)

    def get_object(self, queryset=None):
        return self.exam

    def get(self, request, *args, **kwargs):
        response = HttpResponse(
            FileWrapper(self.exam.exam_file), content_type='application/pdf')
        response['Content-Disposition'] = 'inline;filename="{exam}"'.format(
            exam=smart_bytes(self.exam, encoding='ascii'))
        return response


class ExamReviewListView(ListView):
    """Show all exams that are unverified or have flags."""
    context_object_name = 'exams'
    queryset = Exam.objects.filter(
        Q(blacklisted=False), Q(verified=False) | Q(flags__gt=0))
    template_name = 'exams/review.html'

    @method_decorator(officer_required)
    def dispatch(self, *args, **kwargs):
        return super(ExamReviewListView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ExamReviewListView, self).get_context_data(**kwargs)
        context['unverified_exams'] = Exam.objects.filter(
            verified=False, blacklisted=False)
        context['flagged_exams'] = Exam.objects.filter(
            flags__gt=0, blacklisted=False)
        context['blacklisted_exams'] = Exam.objects.filter(blacklisted=True)
        return context


class ExamEditView(UpdateView):
    form_class = EditForm
    context_object_name = 'exam'
    template_name = 'exams/edit.html'
    exam = None

    @method_decorator(officer_required)
    def dispatch(self, *args, **kwargs):
        self.exam = get_object_or_404(Exam, pk=self.kwargs['exam_pk'])
        return super(ExamEditView, self).dispatch(*args, **kwargs)

    def get_object(self, queryset=None):
        return self.exam

    def get_context_data(self, **kwargs):
        context = super(ExamEditView, self).get_context_data(**kwargs)
        context['flags'] = ExamFlag.objects.filter(exam=self.exam)
        context['permissions'] = InstructorPermission.objects.filter(
            instructor__in=self.exam.instructors)
        return context

    def get_success_url(self):
        return reverse('exams:review')


class ExamDeleteView(DeleteView):
    context_object_name = 'exam'
    template_name = 'exams/delete.html'
    exam = None

    @method_decorator(officer_required)
    def dispatch(self, *args, **kwargs):
        self.exam = get_object_or_404(Exam, pk=self.kwargs['exam_pk'])
        return super(ExamDeleteView, self).dispatch(*args, **kwargs)

    def get_object(self, queryset=None):
        return self.exam

    def form_valid(self, form):
        exam = form.save(commit=False)
        exam.delete()
        return super(ExamDeleteView, self).form_valid(form)

    def get_success_url(self):
        return reverse('exams:review')


class ExamFlagCreateView(CreateView):
    form_class = FlagForm
    template_name = 'exams/flag.html'
    exam = None

    def dispatch(self, *args, **kwargs):
        self.exam = get_object_or_404(Exam, pk=self.kwargs['exam_pk'])
        return super(ExamFlagCreateView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        """Flag exam if valid data is posted."""
        flag = form.save(commit=False)
        flag.exam = self.exam
        flag.save()
        return super(ExamFlagCreateView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(ExamFlagCreateView, self).get_context_data(**kwargs)
        context['exam'] = self.exam
        return context

    def get_success_url(self):
        return reverse('exams:review')


class ExamFlagResolveView(UpdateView):
    form_class = ResolveFlagForm
    context_object_name = 'flag'
    template_name = 'exams/resolve.html'
    flag = None

    @method_decorator(officer_required)
    def dispatch(self, *args, **kwargs):
        self.flag = get_object_or_404(ExamFlag, pk=kwargs['flag_pk'])
        return super(ExamFlagResolveView, self).dispatch(*args, **kwargs)

    def get_object(self, queryset=None):
        return self.flag

    def form_valid(self, form):
        """Resolve flag if valid data is posted."""
        flag = form.save(commit=False)
        flag.resolved = True
        flag.save()
        return super(ExamFlagResolveView, self).form_valid(form)

    def get_success_url(self):
        return reverse('exams:review')


class PermissionEditView(UpdateView):
    form_class = EditPermissionForm
    context_object_name = 'permission'
    template_name = 'exams/permission.html'
    permission = None

    @method_decorator(officer_required)
    def dispatch(self, *args, **kwargs):
        self.permission = get_object_or_404(
            InstructorPermission, pk=self.kwargs['permission_pk'])
        return super(PermissionEditView, self).dispatch(*args, **kwargs)

    def get_object(self, queryset=None):
        return self.permission

    def get_success_url(self):
        return reverse('exams:review')
