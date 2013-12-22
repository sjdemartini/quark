from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.servers.basehttp import FileWrapper
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.encoding import smart_bytes
from django.views.generic import DetailView
from django.views.generic.edit import FormView

from quark.resumes.forms import ResumeForm
from quark.resumes.models import Resume
from quark.shortcuts import get_object_or_none
from quark.user_profiles.models import CollegeStudentInfo


class ResumeEditView(FormView):
    form_class = ResumeForm
    template_name = 'resumes/edit.html'
    resume = None

    @method_decorator(login_required)
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

    def get_success_url(self):
        return reverse('resumes:edit')


class ResumeDownloadView(DetailView):
    """View for downloading resumes."""
    model = Resume

    def get(self, request, *args, **kwargs):
        resume = get_object_or_404(Resume, user=self.request.user)
        response = HttpResponse(
            FileWrapper(resume.resume_file),
            content_type='application/pdf')
        response['Content-Disposition'] = 'inline;filename="{resume}"'.format(
            resume=smart_bytes(
                resume.get_download_file_name(), encoding='ascii'))
        return response
