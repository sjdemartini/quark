from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import ListView
from django.views.generic import UpdateView
from django.views.generic.base import ContextMixin
from django.views.generic.edit import FormView

from quark.base.models import Term
from quark.candidates.models import Candidate
from quark.candidates.models import CandidateRequirement
from quark.candidates.models import CandidateRequirementProgress
from quark.candidates.models import Challenge
from quark.candidates.models import ChallengeType
from quark.candidates.forms import CandidatePhotoForm
from quark.candidates.forms import CandidateRequirementProgressFormSet
from quark.candidates.forms import CandidateRequirementFormSet
from quark.candidates.forms import ChallengeCandidateRequirementForm
from quark.candidates.forms import ChallengeForm
from quark.candidates.forms import ChallengeVerifyFormSet
from quark.candidates.forms import EventCandidateRequirementForm
from quark.candidates.forms import ExamFileCandidateRequirementForm
from quark.candidates.forms import ManualCandidateRequirementForm
from quark.events.models import EventAttendance
from quark.events.models import EventType
from quark.exams.models import Exam


class CandidateContextMixin(ContextMixin):
    """Mixin for getting the candidate, events, challenges, and exams for
    the context dictionary. Used in candidate management and candidate portal.
    """
    def get_context_data(self, **kwargs):
        # pylint: disable=R0914
        context = super(CandidateContextMixin, self).get_context_data(**kwargs)
        candidate = kwargs.get('candidate')
        context['candidate'] = candidate

        attended_events = {}
        event_types = EventType.objects.values_list('name', flat=True)
        for event_type in event_types:
            attended_events[event_type] = []
        attendances = EventAttendance.objects.filter(person=candidate.user)
        for attendance in attendances:
            attended_events[
                attendance.event.event_type.name].append(attendance.event)
        context['events'] = attended_events

        requested_challenges = {}
        challenge_types = ChallengeType.objects.values_list('name', flat=True)
        for challenge_type in challenge_types:
            requested_challenges[challenge_type] = []
        challenges = Challenge.objects.filter(candidate=candidate)
        for challenge in challenges:
            requested_challenges[challenge.challenge_type.name].append(
                challenge)
        context['challenges'] = requested_challenges

        approved_exams = Exam.objects.get_approved().filter(
            submitter=candidate.user)
        context['approved_exams'] = approved_exams
        approved_exam_pks = [exam.pk for exam in approved_exams]
        unapproved_exams = Exam.objects.filter(
            submitter=candidate.user).exclude(pk__in=approved_exam_pks)
        context['unverified_exams'] = unapproved_exams.filter(verified=False)
        # Only include verified exams for blacklisted_exams to prevent showing
        # the same exams twice
        context['blacklisted_exams'] = unapproved_exams.filter(
            blacklisted=True, verified=True)

        return context


class CandidateListView(ListView):
    context_object_name = 'candidates'
    template_name = 'candidates/list.html'
    display_term = None

    @method_decorator(login_required)
    @method_decorator(permission_required(
        'candidates.change_candidate', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        # pylint: disable=R0801
        term = kwargs.get('term', '')
        if not term:
            self.display_term = Term.objects.get_current_term()
        else:
            self.display_term = Term.objects.get_by_url_name(term)
            if self.display_term is None:
                raise Http404
        return super(CandidateListView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        return Candidate.objects.filter(term=self.display_term)

    def get_context_data(self, **kwargs):
        context = super(CandidateListView, self).get_context_data(**kwargs)
        context['terms'] = Term.objects.all()
        context['display_term'] = self.display_term
        return context


class CandidatePhotoView(UpdateView):
    context_object_name = 'candidate'
    form_class = CandidatePhotoForm
    model = Candidate
    pk_url_kwarg = 'candidate_pk'
    template_name = 'candidates/photo.html'

    @method_decorator(login_required)
    @method_decorator(permission_required(
        'candidates.change_candidate', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(CandidatePhotoView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'Candidate photo uploaded!')
        return super(CandidatePhotoView, self).form_valid(form)

    def get_success_url(self):
        return reverse('candidates:edit',
                       kwargs={'candidate_pk': self.object.pk})


class CandidateEditView(FormView, CandidateContextMixin):
    form_class = CandidateRequirementProgressFormSet
    template_name = 'candidates/edit.html'
    candidate = None
    current_term = None
    progress_list = None
    requirements = None

    @method_decorator(login_required)
    @method_decorator(permission_required(
        'candidates.change_candidate', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        self.candidate = get_object_or_404(
            Candidate, pk=self.kwargs['candidate_pk'])
        self.current_term = Term.objects.get_current_term()
        self.requirements = CandidateRequirement.objects.filter(
            term=self.current_term)

        # Create a list of progresses that at each index contains either a
        # progress corresponding to a requirement or None if there is no
        # progress for the corresponding requirement
        self.progress_list = []
        progress_index = 0
        progresses = CandidateRequirementProgress.objects.filter(
            candidate=self.candidate)

        for req in self.requirements:
            # Progresses are ordered the same way as requirements,
            # so all progresses will be correctly checked in the loop
            if progress_index < progresses.count():
                progress = progresses[progress_index]
                if progress.requirement == req:
                    self.progress_list.append(progress)
                    progress_index += 1
                    continue
            self.progress_list.append(None)

        return super(CandidateEditView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs['candidate'] = self.candidate
        context = super(CandidateEditView, self).get_context_data(**kwargs)
        formset = self.get_form(self.form_class)

        # Initialize req_types to contain lists for every requirement type
        req_types = {}
        for req in CandidateRequirement.REQUIREMENT_TYPE_CHOICES:
            req_types[req[0]] = []

        for i in range(self.requirements.count()):
            req = self.requirements[i]
            progress = self.progress_list[i]
            form = formset[i]
            entry = {
                'completed': req.get_progress(self.candidate)[0],
                'requirement': req,
                'form': form}
            form.initial = {
                'manually_recorded_credits': 0,
                'credits_needed': req.credits_needed}

            if progress:
                form.initial = {
                    'manually_recorded_credits': (
                        progress.manually_recorded_credits),
                    'credits_needed': progress.alternate_credits_needed,
                    'comments': progress.comments}
            req_type = req.requirement_type
            req_types[req_type].append(entry)

        context['req_types'] = req_types
        return context

    def form_valid(self, form):
        """Check every form individually in the formset, and create or edit
        progresses if necessary.
        """
        for i in range(self.requirements.count()):
            requirement = self.requirements[i]
            progress = self.progress_list[i]
            current_form = form[i]

            manually_recorded_credits = (current_form.cleaned_data.
                                         get('manually_recorded_credits'))
            credits_needed = current_form.cleaned_data.get('credits_needed')
            comments = current_form.cleaned_data.get('comments')

            if progress:
                # Update the progress that already exists
                progress.manually_recorded_credits = (
                    manually_recorded_credits)
                progress.alternate_credits_needed = credits_needed
                progress.comments = comments
                progress.save()
            else:
                # Create a new progress based on the form fields only if a
                # new progress needs to be created
                if ((credits_needed != requirement.credits_needed or
                     manually_recorded_credits != 0)):
                    CandidateRequirementProgress.objects.get_or_create(
                        candidate=self.candidate,
                        requirement=requirement,
                        manually_recorded_credits=manually_recorded_credits,
                        alternate_credits_needed=credits_needed,
                        comments=comments)

        messages.success(self.request, 'Changes saved!')
        return super(CandidateEditView, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct your input fields.')
        return super(CandidateEditView, self).form_invalid(form)

    def get_success_url(self):
        return reverse(
            'candidates:edit', kwargs={'candidate_pk': self.candidate.pk})


class ChallengeVerifyView(FormView):
    form_class = ChallengeVerifyFormSet
    template_name = 'candidates/challenges.html'
    current_term = None

    @method_decorator(login_required)
    @method_decorator(permission_required(
        'candidates.change_challenge', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        self.current_term = Term.objects.get_current_term()
        return super(ChallengeVerifyView, self).dispatch(*args, **kwargs)

    def get_form_kwargs(self, **kwargs):
        """Set the user in the form."""
        kwargs = super(ChallengeVerifyView, self).get_form_kwargs(**kwargs)
        kwargs['user'] = self.request.user
        return kwargs

    def get_form(self, form_class):
        """Initialize each form in the formset with a challenge."""
        formset = super(ChallengeVerifyView, self).get_form(form_class)
        challenges = Challenge.objects.filter(
            verifying_user=self.request.user, candidate__term=self.current_term)
        for i in range(challenges.count()):
            formset[i].instance = challenges[i]
            formset[i].initial = {'verified': challenges[i].verified}
        return formset

    def get_context_data(self, **kwargs):
        context = super(ChallengeVerifyView, self).get_context_data(
            **kwargs)
        context['term'] = self.current_term
        return context

    def form_valid(self, form):
        """Check every form individually in the formset."""
        for challenge_form in form:
            challenge_form.save()
        messages.success(self.request, 'Changes saved!')
        return super(ChallengeVerifyView, self).form_valid(form)

    def get_success_url(self):
        return reverse('candidates:challenges')


class CandidateRequirementsEditView(FormView):
    form_class = CandidateRequirementFormSet
    template_name = 'candidates/edit_requirements.html'
    current_term = None
    requirements = None

    @method_decorator(login_required)
    @method_decorator(permission_required(
        'candidates.change_candidaterequirement', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        self.current_term = Term.objects.get_current_term()
        self.requirements = CandidateRequirement.objects.filter(
            term=self.current_term)
        return super(CandidateRequirementsEditView, self).dispatch(
            *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CandidateRequirementsEditView, self).get_context_data(
            **kwargs)
        context['term'] = self.current_term
        formset = self.get_form(self.form_class)

        # Initialize req_forms to contain lists for every requirement type
        req_forms = {}
        for req in CandidateRequirement.REQUIREMENT_TYPE_CHOICES:
            req_forms[req[0]] = []

        for i in range(self.requirements.count()):
            current_form = formset[i]
            current_req = self.requirements[i]
            current_form.instance = current_req
            current_form.initial = {
                'credits_needed': current_req.credits_needed}
            req_type = current_req.requirement_type
            req_forms[req_type].append(current_form)

        context['req_forms'] = req_forms
        return context

    def form_valid(self, form):
        """Check every form individually in the formset."""
        for i in range(self.requirements.count()):
            req = self.requirements[i]
            credits_needed = form[i].cleaned_data.get('credits_needed')
            req.credits_needed = credits_needed
            req.save()
        messages.success(self.request, 'Changes saved!')
        return super(CandidateRequirementsEditView, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct your input fields.')
        return super(CandidateRequirementsEditView, self).form_invalid(form)

    def get_success_url(self):
        return reverse('candidates:edit-requirements')


class CandidateRequirementCreateView(CreateView):
    template_name = 'candidates/add_requirement.html'
    requirement_type = None
    display_req_type = None

    @method_decorator(login_required)
    @method_decorator(permission_required(
        'candidates.add_candidaterequirement', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        self.requirement_type = kwargs.get('req_type', '')
        return super(CandidateRequirementCreateView, self).dispatch(
            *args, **kwargs)

    def get_form_class(self):
        """Set the form class based on the candidate requirement type."""
        if self.requirement_type == CandidateRequirement.EVENT:
            self.display_req_type = 'Event'
            return EventCandidateRequirementForm
        elif self.requirement_type == CandidateRequirement.CHALLENGE:
            self.display_req_type = 'Challenge'
            return ChallengeCandidateRequirementForm
        elif self.requirement_type == CandidateRequirement.EXAM_FILE:
            self.display_req_type = 'Exam File'
            return ExamFileCandidateRequirementForm
        elif self.requirement_type == CandidateRequirement.MANUAL:
            self.display_req_type = 'Manual'
            return ManualCandidateRequirementForm
        else:
            raise Http404

    def get_context_data(self, **kwargs):
        context = super(CandidateRequirementCreateView, self).get_context_data(
            **kwargs)
        context['requirement_type'] = self.requirement_type
        context['display_req_type'] = self.display_req_type
        return context

    def form_valid(self, form):
        """Set the term of the requirement to the current term."""
        form.instance.term = Term.objects.get_current_term()
        messages.success(self.request, '{req_type} requirement created!'.format(
            req_type=self.display_req_type))
        return super(CandidateRequirementCreateView, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct your input fields.')
        return super(CandidateRequirementCreateView, self).form_invalid(form)

    def get_success_url(self):
        return reverse('candidates:edit-requirements')


class CandidateRequirementDeleteView(DeleteView):
    context_object_name = 'requirement'
    model = CandidateRequirement
    pk_url_kwarg = 'req_pk'
    template_name = 'candidates/delete_requirement.html'

    @method_decorator(login_required)
    @method_decorator(permission_required(
        'candidates.delete_candidaterequirement', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(CandidateRequirementDeleteView, self).dispatch(
            *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'Candidate requirement deleted!')
        return super(CandidateRequirementDeleteView, self).form_valid(form)

    def get_success_url(self):
        return reverse('candidates:edit-requirements')


class CandidatePortalView(CreateView, CandidateContextMixin):
    """The view for the candidate portal, which is also used for creating
    challenges.
    """
    form_class = ChallengeForm
    template_name = 'candidates/portal.html'
    candidate = None
    current_term = None

    @method_decorator(login_required)
    # TODO(ericdwang): Make sure that only candidates can access this view
    def dispatch(self, *args, **kwargs):
        self.current_term = Term.objects.get_current_term()
        self.candidate = get_object_or_404(
            Candidate, user=self.request.user, term=self.current_term)
        return super(CandidatePortalView, self).dispatch(
            *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs['candidate'] = self.candidate
        context = super(CandidatePortalView, self).get_context_data(**kwargs)
        requirements = CandidateRequirement.objects.filter(
            term=self.current_term)
        progresses = CandidateRequirementProgress.objects.filter(
            candidate=self.candidate)
        progress_index = 0

        # Initialize req_types to contain lists for every requirement type
        req_types = {}
        for req in CandidateRequirement.REQUIREMENT_TYPE_CHOICES:
            req_types[req[0]] = []

        for i in range(requirements.count()):
            req = requirements[i]
            entry = {
                'requirement': req,
                'completed': req.get_progress(self.candidate)[0],
                'credits_needed': req.credits_needed}

            # Progresses are ordered the same way as requirements,
            # so all progresses will be correctly checked in the loop
            if progress_index < progresses.count():
                current_progress = progresses[progress_index]
                if current_progress.requirement == req:
                    entry['credits_needed'] = (
                        current_progress.alternate_credits_needed)
                    progress_index += 1
            req_type = req.requirement_type
            req_types[req_type].append(entry)

        context['req_types'] = req_types
        return context

    def form_valid(self, form):
        """Set the candidate of the challenge to the requester."""
        form.instance.candidate = self.candidate
        messages.success(self.request, 'Challenge requested!')
        return super(CandidatePortalView, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct your input fields.')
        return super(CandidatePortalView, self).form_invalid(form)

    def get_success_url(self):
        return reverse('candidates:portal')
