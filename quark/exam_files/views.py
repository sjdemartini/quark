from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import ListView
from django.views.generic import UpdateView

from quark.auth.decorators import officer_required
from quark.exam_files.forms import ExamForm
from quark.exam_files.forms import FlagForm
from quark.exam_files.forms import ResolveFlagForm
from quark.exam_files.forms import UploadForm
from quark.exam_files.models import Exam


# TODO(ericdwang): re-add get_success_url when templates are created
class ExamUploadView(CreateView):
    form_class = UploadForm
    template_name = 'exam_files/upload.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ExamUploadView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        """Assign submitter to the exam."""
        exam = form.save(commit=False)
        exam.submitter = self.request.user
        exam.save()
        return super(ExamUploadView, self).form_valid(form)


class ExamListView(ListView):
    context_object_name = 'exam_list'
    template_name = 'exam_files/list.html'
    short_name = None
    number = None

    def dispatch(self, *args, **kwargs):
        self.short_name = kwargs['short_name']
        self.number = kwargs['number']
        return super(ExamListView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        """Return a query set of all exam files based on the
        department and course number.
        """
        query = Exam.objects.filter(
            courseinstance__course__department__short_name=self.short_name,
            courseinstance__course__number=self.number,
            approved=True)
        if not query.exists():
            raise Http404
        return query


class ExamReviewListView(ListView):
    """Show all not blacklisted exams that are unapproved or have flags."""
    context_object_name = 'exam_review'
    queryset = Exam.objects.filter(
        Q(blacklisted=False), Q(approved=False) | Q(flags__gt=0))
    template_name = 'exam_files/review.html'

    @method_decorator(officer_required)
    def dispatch(self, *args, **kwargs):
        return super(ExamReviewListView, self).dispatch(*args, **kwargs)


class ExamEditView(UpdateView):
    form_class = ExamForm
    pk_url_kwarg = 'exam_id'
    template_name = 'exam_files/edit.html'

    @method_decorator(officer_required)
    def dispatch(self, *args, **kwargs):
        return super(ExamEditView, self).dispatch(*args, **kwargs)


class ExamDeleteView(DeleteView):
    model = Exam
    context_object_name = 'delete_exam'
    template_name = 'exam_files/delete.html'

    @method_decorator(officer_required)
    def dispatch(self, *args, **kwargs):
        return super(ExamDeleteView, self).dispatch(*args, **kwargs)


class ExamFlagCreateView(CreateView):
    form_class = FlagForm
    template_name = 'exam_files/flag.html'
    exam_id = None

    def dispatch(self, *args, **kwargs):
        self.exam_id = kwargs['exam_id']
        return super(ExamFlagCreateView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        """Flag exam if valid data is posted."""
        flag = form.save(commit=False)
        flag.exam = get_object_or_404(Exam, pk=self.exam_id)
        flag.save()
        return super(ExamFlagCreateView, self).form_valid(form)


class ExamFlagResolveView(UpdateView):
    form_class = ResolveFlagForm
    template_name = 'exam_files/resolve_flag.html'
    exam_id = None

    @method_decorator(officer_required)
    def dispatch(self, *args, **kwargs):
        self.exam_id = kwargs['exam_id']
        return super(ExamFlagResolveView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        """Resolve flag if valid data is posted."""
        flag = form.save(commit=False)
        flag.resolved = True
        flag.save()
        return super(ExamFlagResolveView, self).form_valid(form)
