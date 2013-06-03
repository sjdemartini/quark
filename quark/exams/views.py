from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import ListView
from django.views.generic import UpdateView

from quark.auth.decorators import officer_required
from quark.exams.forms import ExamForm
from quark.exams.forms import FlagForm
from quark.exams.forms import ResolveFlagForm
from quark.exams.forms import UploadForm
from quark.exams.models import Exam


# TODO(ericdwang): re-add get_success_url when templates are created
class ExamUploadView(CreateView):
    form_class = UploadForm
    template_name = 'exams/upload.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ExamUploadView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        """Assign submitter to the exam."""
        exam = form.save(commit=False)
        exam.submitter = self.request.user
        exam.save()
        return super(ExamUploadView, self).form_valid(form)


class ExamReviewListView(ListView):
    """Show all non-blacklisted exams that are unverified or have flags."""
    context_object_name = 'exam_review'
    queryset = Exam.objects.filter(
        Q(blacklisted=False), Q(verified=False) | Q(flags__gt=0))
    template_name = 'exams/review.html'

    @method_decorator(officer_required)
    def dispatch(self, *args, **kwargs):
        return super(ExamReviewListView, self).dispatch(*args, **kwargs)


class ExamEditView(UpdateView):
    form_class = ExamForm
    pk_url_kwarg = 'exam_id'
    template_name = 'exams/edit.html'

    @method_decorator(officer_required)
    def dispatch(self, *args, **kwargs):
        return super(ExamEditView, self).dispatch(*args, **kwargs)


class ExamDeleteView(DeleteView):
    model = Exam
    context_object_name = 'delete_exam'
    template_name = 'exams/delete.html'

    @method_decorator(officer_required)
    def dispatch(self, *args, **kwargs):
        return super(ExamDeleteView, self).dispatch(*args, **kwargs)


class ExamFlagCreateView(CreateView):
    form_class = FlagForm
    template_name = 'exams/flag.html'
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
    template_name = 'exams/resolve_flag.html'
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
