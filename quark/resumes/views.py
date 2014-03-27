from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import PermissionDenied
from django.core.servers.basehttp import FileWrapper
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.encoding import smart_bytes
from django.views.generic import DetailView
from django.views.generic.edit import FormView

from quark.resumes.forms import ResumeForm
from quark.resumes.forms import ResumeListFormSet
from quark.resumes.forms import ResumeCritiqueFormSet
from quark.resumes.forms import ResumeVerifyFormSet
from quark.resumes.models import Resume
from quark.shortcuts import get_object_or_none
from quark.user_profiles.models import CollegeStudentInfo


class ResumeViewMixin(object):
    """Mixin for viewing resumes and their stats, as well as saving changes to
    resumes. Subclasses should be FormViews.
    """
    @method_decorator(login_required)
    @method_decorator(
        permission_required('resumes.change_resume', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(ResumeViewMixin, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        for resume_form in form:
            resume_form.save()
        messages.success(self.request, 'Changes saved!')
        return super(ResumeViewMixin, self).form_valid(form)


class ResumeListView(ResumeViewMixin, FormView):
    """List all resumes and their basic stats."""
    form_class = ResumeListFormSet
    success_url = reverse_lazy('resumes:list')
    template_name = 'resumes/list.html'

    def get_form(self, form_class):
        formset = super(ResumeListView, self).get_form(form_class)
        resumes = Resume.objects.select_related(
            'user__userprofile', 'user__collegestudentinfo',
            'user__collegestudentinfo__grad_term').prefetch_related(
            'user__collegestudentinfo__major')
        for i, resume in enumerate(resumes):
            formset[i].instance = resume
            formset[i].initial = {'verified': resume.verified}
        return formset

    def get_context_data(self, **kwargs):
        context = super(ResumeListView, self).get_context_data(**kwargs)
        context['all'] = True
        return context


class ResumeVerifyView(ResumeViewMixin, FormView):
    """List all resumes awaiting verification and allow for verifying."""
    form_class = ResumeVerifyFormSet
    success_url = reverse_lazy('resumes:verify')
    template_name = 'resumes/verify.html'

    def get_form(self, form_class):
        formset = super(ResumeVerifyView, self).get_form(form_class)
        resumes = Resume.objects.filter(verified__isnull=True).select_related(
            'user__userprofile', 'user__collegestudentinfo',
            'user__collegestudentinfo__grad_term',
            'user__studentorguserprofile__initiation_term').prefetch_related(
            'user__collegestudentinfo__major')
        for i, resume in enumerate(resumes):
            formset[i].instance = resume
            formset[i].initial = {'verified': resume.verified}
        return formset

    def get_context_data(self, **kwargs):
        context = super(ResumeVerifyView, self).get_context_data(**kwargs)
        context['verify'] = True
        return context


class ResumeCritiqueView(ResumeViewMixin, FormView):
    """List all resumes awaiting critique and allow for checking them off."""
    form_class = ResumeCritiqueFormSet
    success_url = reverse_lazy('resumes:critique')
    template_name = 'resumes/critique.html'

    def get_form(self, form_class):
        formset = super(ResumeCritiqueView, self).get_form(form_class)
        resumes = Resume.objects.filter(critique=True).select_related(
            'user__userprofile', 'user__collegestudentinfo',
            'user__collegestudentinfo__grad_term',
            'user__studentorguserprofile__initiation_term').prefetch_related(
            'user__collegestudentinfo__major')
        for i, resume in enumerate(resumes):
            formset[i].instance = resume
            # display the inverse of the value stored in resume.critique
            # for the "critique completed" column.
            formset[i].initial = {'critique': not resume.critique}
        return formset

    def get_context_data(self, **kwargs):
        context = super(ResumeCritiqueView, self).get_context_data(**kwargs)
        context['critique'] = True
        return context


class ResumeEditView(FormView):
    form_class = ResumeForm
    success_url = reverse_lazy('resumes:edit')
    template_name = 'resumes/edit.html'
    resume = None

    @method_decorator(login_required)
    @method_decorator(
        permission_required('resumes.add_resume', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        self.resume = get_object_or_none(Resume, user=self.request.user)
        return super(ResumeEditView, self).dispatch(*args, **kwargs)

    def get_form(self, form_class):
        form = super(ResumeEditView, self).get_form(form_class)
        if self.resume:
            form.instance = self.resume
            form.initial = {
                'gpa': self.resume.gpa,
                'full_text': self.resume.full_text,
                'critique': self.resume.critique,
                'release': self.resume.release}
        return form

    def get_context_data(self, **kwargs):
        context = super(ResumeEditView, self).get_context_data(**kwargs)
        if self.resume:
            context['resume'] = self.resume
        context['info'] = get_object_or_none(
            CollegeStudentInfo, user=self.request.user)
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.verified = None
        form.instance.save()
        messages.success(self.request, 'Changes saved!')
        return super(ResumeEditView, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct your input fields.')
        return super(ResumeEditView, self).form_invalid(form)


class ResumeDownloadView(DetailView):
    """View for downloading resumes."""
    model = Resume
    user = None

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        if 'user_pk' in self.kwargs:
            # Check whether the user has permission to view other people's
            # resumes
            if not self.request.user.has_perm('resumes.view_resumes'):
                raise PermissionDenied

            self.user = get_object_or_404(
                get_user_model(), pk=self.kwargs['user_pk'])
        else:
            self.user = self.request.user
        return super(ResumeDownloadView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        resume = get_object_or_404(Resume, user=self.user)
        response = HttpResponse(
            FileWrapper(resume.resume_file),
            content_type='application/pdf')
        response['Content-Disposition'] = 'inline;filename="{resume}"'.format(
            resume=smart_bytes(
                resume.get_download_file_name(), encoding='ascii'))
        return response
