from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.core.servers.basehttp import FileWrapper
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.utils.encoding import smart_bytes
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView

from quark.exams.forms import EditForm
from quark.exams.forms import FlagForm
from quark.exams.forms import FlagResolveForm
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
        """Assign submitter to the exam."""
        form.instance.submitter = self.request.user
        messages.success(
            self.request, 'Exam uploaded! It will need to verified first '
            'before it becomes visible to everyone.')
        return super(ExamUploadView, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct your input fields.')
        return super(ExamUploadView, self).form_invalid(form)

    def get_success_url(self):
        return reverse('courses:course-department-list')


class ExamDownloadView(DetailView):
    """View for downloading exams."""
    model = Exam
    object = None
    pk_url_kwarg = 'exam_pk'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        response = HttpResponse(
            FileWrapper(self.object.exam_file),
            content_type='application/pdf')
        response['Content-Disposition'] = 'inline;filename="{exam}"'.format(
            exam=smart_bytes(
                self.object.get_download_file_name(), encoding='ascii'))
        return response


class ExamReviewListView(ListView):
    """Show all exams that are unverified or have flags."""
    context_object_name = 'exams'
    template_name = 'exams/review.html'
    flagged_exams = None
    unverified_exams = None

    @method_decorator(login_required)
    @method_decorator(
        permission_required('exams.change_exam', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        non_blacklisted_exams = Exam.objects.filter(blacklisted=False)
        self.unverified_exams = non_blacklisted_exams.filter(verified=False)
        self.flagged_exams = non_blacklisted_exams.filter(flags__gt=0)
        return super(ExamReviewListView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        return (self.unverified_exams | self.flagged_exams).select_related(
            'course_instance__term',
            'course_instance__course__department').prefetch_related(
            'course_instance__instructors')

    def get_context_data(self, **kwargs):
        context = super(ExamReviewListView, self).get_context_data(**kwargs)
        context['unverified_exam_count'] = self.unverified_exams.count()
        context['flagged_exam_count'] = self.flagged_exams.count()
        context['blacklisted_exams'] = Exam.objects.filter(
            blacklisted=True).select_related(
            'course_instance__term',
            'course_instance__course__department').prefetch_related(
            'course_instance__instructors')
        return context


class ExamEditView(UpdateView):
    form_class = EditForm
    context_object_name = 'exam'
    template_name = 'exams/edit.html'
    exam = None

    @method_decorator(login_required)
    @method_decorator(
        permission_required('exams.change_exam', raise_exception=True))
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

    def form_valid(self, form):
        messages.success(self.request, 'Changes saved!')
        return super(ExamEditView, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct your input fields.')
        return super(ExamEditView, self).form_invalid(form)

    def get_success_url(self):
        return reverse('exams:edit', kwargs={'exam_pk': self.exam.pk})


class ExamDeleteView(DeleteView):
    context_object_name = 'exam'
    model = Exam
    pk_url_kwarg = 'exam_pk'
    template_name = 'exams/delete.html'

    @method_decorator(login_required)
    @method_decorator(
        permission_required('exams.delete_exam', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(ExamDeleteView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'Exam deleted!')
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

    def get_context_data(self, **kwargs):
        context = super(ExamFlagCreateView, self).get_context_data(**kwargs)
        context['exam'] = self.exam
        return context

    def form_valid(self, form):
        """Flag exam if valid data is posted."""
        form.instance.exam = self.exam
        messages.success(self.request, 'Exam flag created!')
        return super(ExamFlagCreateView, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct your input fields.')
        return super(ExamFlagCreateView, self).form_invalid(form)

    def get_success_url(self):
        """Go to the course page corresponding to the flagged exam."""
        return reverse('courses:detail',
                       kwargs={'dept_slug': self.exam.course.department.slug,
                               'course_num': self.exam.course.number})


class ExamFlagResolveView(UpdateView):
    form_class = FlagResolveForm
    context_object_name = 'flag'
    model = ExamFlag
    object = None
    pk_url_kwarg = 'flag_pk'
    template_name = 'exams/resolve.html'

    @method_decorator(login_required)
    @method_decorator(
        permission_required('exams.change_examflag', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(ExamFlagResolveView, self).dispatch(*args, **kwargs)

    def get(self, *args, **kwargs):
        self.object = self.get_object()  # get the flag object

        # If the exam pk provided in the URL doesn't match the exam for which
        # this flag is addressing, redirect to the proper address for the flag
        if self.kwargs['exam_pk'] != str(self.object.exam.pk):
            return redirect('exams:flag-resolve', exam_pk=self.object.exam.pk,
                            flag_pk=self.object.pk)
        else:
            return super(ExamFlagResolveView, self).get(self, *args, **kwargs)

    def form_valid(self, form):
        """Resolve flag if valid data is posted."""
        form.instance.resolved = True
        messages.success(self.request, 'Exam flag resolved!')
        return super(ExamFlagResolveView, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct your input fields.')
        return super(ExamFlagResolveView, self).form_invalid(form)

    def get_success_url(self):
        return reverse('exams:edit', kwargs={'exam_pk': self.kwargs['exam_pk']})
