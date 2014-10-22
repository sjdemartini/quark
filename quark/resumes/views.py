import mimetypes

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMessage
from django.core.servers.basehttp import FileWrapper
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.encoding import smart_bytes
from django.views.generic import DetailView
from django.views.generic.edit import FormView

from quark.base.models import Officer
from quark.base.models import OfficerPosition
from quark.base.models import Term
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
        form.instance.updated = timezone.now()
        form.instance.save()
        new_resume = form.instance
        if new_resume.critique:
            responsible_committee = OfficerPosition.objects.get(
                short_name=settings.RESUMEQ_OFFICER_POSITION)
            officers = Officer.objects.filter(
                term=Term.objects.get_current_term(),
                position=responsible_committee)
            if officers.exists():
                assignee = officers[new_resume.id %
                                    officers.count()].user
                assignee_name = assignee.userprofile.get_verbose_full_name()
                requestee = self.request.user
                requestee_name = requestee.userprofile.get_verbose_full_name()
                subject = 'Resume critique requested by {}'.format(
                    requestee_name)
                assigning_body = render_to_string(
                    'resumes/resume_assignment_email.html',
                    {'assignee': assignee_name,
                     'requestee': requestee_name,
                     'committee': responsible_committee.short_name,
                     'user': requestee})
                assigning_message = EmailMessage(
                    subject=subject,
                    body=assigning_body,
                    from_email=settings.RESUMEQ_ADDRESS,
                    to=[assignee.email],
                    cc=[settings.RESUMEQ_ADDRESS])
                assigning_message.send(fail_silently=True)
                confirmation_body = render_to_string(
                    'resumes/resume_confirmation_email.html',
                    {'requestee': requestee_name,
                     'committee': responsible_committee.long_name}
                    )
                confirmation_message = EmailMessage(
                    subject=subject,
                    body=confirmation_body,
                    from_email=settings.RESUMEQ_ADDRESS,
                    to=[requestee.email],
                    cc=[settings.RESUMEQ_ADDRESS])
                m_id = assigning_message.extra_headers.get('Message-Id', None)
                confirmation_message.extra_headers = {'References': m_id,
                                                      'In-Reply-To': m_id}
                confirmation_message.send(fail_silently=True)
            messages.success(self.request,
                             'Your resume critique request has been sent!')
        else:
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
        mime_type, _ = mimetypes.guess_type(resume.resume_file.name)
        response = HttpResponse(
            FileWrapper(resume.resume_file),
            content_type=mime_type)
        response['Content-Disposition'] = 'inline;filename="{resume}"'.format(
            resume=smart_bytes(
                resume.get_download_file_name(), encoding='ascii'))
        return response
