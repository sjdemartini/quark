import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import CreateView
from django.views.generic import ListView
from django.views.generic import UpdateView
from django.views.generic.base import ContextMixin
from django.views.generic.edit import FormView

from quark.base.models import Term
from quark.base.views import TermParameterMixin
from quark.candidates.models import Candidate
from quark.candidates.models import CandidateRequirement
from quark.candidates.models import CandidateRequirementProgress
from quark.candidates.models import Challenge
from quark.candidates.models import ChallengeType
from quark.candidates.models import ChallengeCandidateRequirement
from quark.candidates.models import EventCandidateRequirement
from quark.candidates.models import ExamFileCandidateRequirement
from quark.candidates.models import ManualCandidateRequirement
from quark.candidates.models import ResumeCandidateRequirement
from quark.candidates.forms import CandidatePhotoForm
from quark.candidates.forms import CandidateRequirementProgressFormSet
from quark.candidates.forms import CandidateRequirementFormSet
from quark.candidates.forms import ChallengeForm
from quark.candidates.forms import ChallengeVerifyFormSet
from quark.candidates.forms import ManualCandidateRequirementForm
from quark.events.models import EventAttendance
from quark.events.models import EventSignUp
from quark.events.models import EventType
from quark.exams.models import Exam
from quark.shortcuts import get_object_or_none
from quark.utils.ajax import json_response


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
        signed_up_events = {}
        elective_events = []

        event_types = EventType.objects.values_list('name', flat=True)
        for event_type in event_types:
            attended_events[event_type] = []
            signed_up_events[event_type] = []
        attendances = EventAttendance.objects.select_related(
            'event__event_type').filter(
            user=candidate.user, event__term=candidate.term)
        signups = EventSignUp.objects.select_related(
            'event__event_type').filter(
            user=candidate.user, event__term=candidate.term,
            unsignup=False).exclude(event__in=attendances.values_list(
            'event', flat=True))
        for attendance in attendances:
            attended_events[
                attendance.event.event_type.name].append(attendance.event)
        for signup in signups:
            signed_up_events[
                signup.event.event_type.name].append(signup.event)

        event_reqs = CandidateRequirement.objects.filter(
            term=candidate.term,
            requirement_type=CandidateRequirement.EVENT)
        try:
            elective_req = event_reqs.get(
                eventcandidaterequirement__event_type__name='Elective')
        except CandidateRequirement.DoesNotExist:
            elective_req = None

        # If at least 1 elective event is required, extra events from other
        # event types will count as elective events.
        if (elective_req and
                elective_req.get_progress(self.candidate)['required'] > 0):
            for event_req in event_reqs:
                req_progress = event_req.get_progress(self.candidate)
                event_type = event_req.eventcandidaterequirement.event_type
                extra = req_progress['completed'] - req_progress['required']
                if extra > 0 and event_type.eligible_elective:
                    elective_events += attended_events[event_type.name][
                        req_progress['required']:]
                    attended_events[event_type.name] = attended_events[
                        event_type.name][:req_progress['required']]

        context['attended_events'] = attended_events
        context['signed_up_events'] = signed_up_events
        context['elective_events'] = elective_events

        requested_challenges = {}
        challenge_types = ChallengeType.objects.values_list('name', flat=True)
        for challenge_type in challenge_types:
            requested_challenges[challenge_type] = []
        challenges = Challenge.objects.select_related(
            'challenge_type', 'verifying_user__userprofile').filter(
            candidate=candidate)
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
        context['blacklisted_exams'] = unapproved_exams.filter(
            blacklisted=True, verified=True)

        return context


class CandidateListView(TermParameterMixin, ListView):
    context_object_name = 'candidates'
    template_name = 'candidates/list.html'

    @method_decorator(login_required)
    @method_decorator(permission_required(
        'candidates.change_candidate', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(CandidateListView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        return Candidate.objects.filter(term=self.display_term).select_related(
            'user__userprofile', 'user__collegestudentinfo').prefetch_related(
            'user__collegestudentinfo__major')


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
    progress_list = None
    requirements = None

    @method_decorator(login_required)
    @method_decorator(permission_required(
        'candidates.change_candidate', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        self.candidate = get_object_or_404(
            Candidate, pk=self.kwargs['candidate_pk'])
        self.requirements = CandidateRequirement.objects.filter(
            term=self.candidate.term).select_related(
            'eventcandidaterequirement',
            'eventcandidaterequirement__event_type',
            'challengecandidaterequirement',
            'challengecandidaterequirement__challenge_type',
            'examfilecandidaterequirement')

        # Create a list of progresses that at each index contains either a
        # progress corresponding to a requirement or None if there is no
        # progress for the corresponding requirement
        self.progress_list = []
        progress_index = 0
        progresses = CandidateRequirementProgress.objects.filter(
            candidate=self.candidate)
        num_progresses = progresses.count()

        for req in self.requirements:
            # Progresses are ordered the same way as requirements,
            # so all progresses will be correctly checked in the loop
            if progress_index < num_progresses:
                progress = progresses[progress_index]
                if progress.requirement == req:
                    self.progress_list.append(progress)
                    progress_index += 1
                    continue
            self.progress_list.append(None)

        return super(CandidateEditView, self).dispatch(*args, **kwargs)

    def get_form_kwargs(self, **kwargs):
        """Set the term in the form."""
        kwargs = super(CandidateEditView, self).get_form_kwargs(**kwargs)
        kwargs['candidate_term'] = self.candidate.term
        return kwargs

    def get_context_data(self, **kwargs):
        kwargs['candidate'] = self.candidate
        context = super(CandidateEditView, self).get_context_data(**kwargs)
        formset = self.get_form(self.form_class)

        # Initialize req_types to contain lists for every requirement type
        req_types = {}
        for req in CandidateRequirement.REQUIREMENT_TYPE_CHOICES:
            req_types[req[0]] = []

        electives_required = Candidate.are_electives_required(self.candidate)

        for i, req in enumerate(self.requirements):
            progress = self.progress_list[i]
            form = formset[i]
            req_progress = req.get_progress(self.candidate)
            completed = req_progress['completed']
            credits_needed = req_progress['required']

            # this is here so on the candidate portal, it will only show
            # something like 3/3 events completed instead of 5/3 if
            # they have more than needed, since 2 of those 5 would be in
            # the electives section (unless electives arent required)
            if electives_required and completed > credits_needed:
                completed = credits_needed

            entry = {
                'completed': completed,
                'credits_needed': credits_needed,
                'requirement': req,
                'form': form
            }
            form.initial['alternate_credits_needed'] = credits_needed
            form.initial['manually_recorded_credits'] = 0
            if progress:
                form.instance = progress
                form.initial['comments'] = progress.comments
                form.initial['manually_recorded_credits'] = completed

            req_type = req.requirement_type
            req_types[req_type].append(entry)

        context['req_types'] = req_types
        return context

    def form_valid(self, form):
        """Check every form individually in the formset:

        Do nothing if a progress doesn't exist and credits_needed == 0
        Create a progress if one doesn't exist and credits_needed != 0
        Edit a progress if one exists and credits_needed != 0
        """
        for i, requirement in enumerate(self.requirements):
            current_form = form[i]
            progress = self.progress_list[i]
            manually_recorded_credits = current_form.cleaned_data.get(
                'manually_recorded_credits')
            alternate_credits_needed = current_form.cleaned_data.get(
                'alternate_credits_needed')
            comments = current_form.cleaned_data.get('comments')

            if ((alternate_credits_needed != requirement.credits_needed or
                 manually_recorded_credits != 0)):
                if progress:
                    # Update the progress that already exists
                    progress.manually_recorded_credits = (
                        manually_recorded_credits)
                    progress.alternate_credits_needed = alternate_credits_needed
                    progress.comments = comments
                    progress.save()
                else:
                    # Create a new progress based on the form fields only if a
                    # new progress needs to be created
                    current_form.instance.candidate = self.candidate
                    current_form.instance.requirement = requirement
                    current_form.save()
        messages.success(self.request, 'Changes saved!')
        return super(CandidateEditView, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct your input fields.')
        return super(CandidateEditView, self).form_invalid(form)

    def get_success_url(self):
        return reverse(
            'candidates:edit', kwargs={'candidate_pk': self.candidate.pk})


class ChallengeVerifyView(TermParameterMixin, FormView):
    form_class = ChallengeVerifyFormSet
    template_name = 'candidates/challenges.html'

    @method_decorator(login_required)
    @method_decorator(permission_required(
        'candidates.change_challenge', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(ChallengeVerifyView, self).dispatch(*args, **kwargs)

    def get_form_kwargs(self, **kwargs):
        """Set the user and term in the form."""
        kwargs = super(ChallengeVerifyView, self).get_form_kwargs(**kwargs)
        kwargs['display_term'] = self.display_term
        kwargs['user'] = self.request.user
        return kwargs

    def get_form(self, form_class):
        """Initialize each form in the formset with a challenge."""
        formset = super(ChallengeVerifyView, self).get_form(form_class)
        challenges = Challenge.objects.select_related(
            'candidate__user__userprofile', 'challenge_type').filter(
            verifying_user=self.request.user, candidate__term=self.display_term)
        for i, challenge in enumerate(challenges):
            formset[i].instance = challenge
            formset[i].initial = {
                'verified': challenges[i].verified,
                'reason': challenges[i].reason}
        return formset

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
    challenge_types = None
    current_term = None
    event_types = None
    req_lists = None

    @method_decorator(login_required)
    @method_decorator(permission_required(
        'candidates.add_candidaterequirement',
        'candidates.change_candidaterequirement', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        self.current_term = Term.objects.get_current_term()
        self.event_types = EventType.objects.all()
        self.challenge_types = ChallengeType.objects.all()

        # Initialize req_lists to contain lists for every requirement type
        self.req_lists = {}
        for req in CandidateRequirement.REQUIREMENT_TYPE_CHOICES:
            self.req_lists[req[0]] = []

        event_reqs = EventCandidateRequirement.objects.filter(
            term=self.current_term)
        # Create a list of requirements that at each index contains either a
        # requirement corresponding to an event type or None if there is no
        # requirement for the corresponding event type
        req_index = 0
        for event_type in self.event_types:
            if req_index < event_reqs.count():
                req = event_reqs[req_index]
                if req.event_type == event_type:
                    self.req_lists[CandidateRequirement.EVENT].append(req)
                    req_index += 1
                    continue
            self.req_lists[CandidateRequirement.EVENT].append(None)

        challenge_reqs = ChallengeCandidateRequirement.objects.filter(
            term=self.current_term)
        # Create a list of requirements that at each index contains either a
        # requirement corresponding to an challenge type or None if there is no
        # requirement for the corresponding challenge type
        req_index = 0
        for challenge_type in self.challenge_types:
            if req_index < challenge_reqs.count():
                req = challenge_reqs[req_index]
                if req.challenge_type == challenge_type:
                    self.req_lists[CandidateRequirement.CHALLENGE].append(req)
                    req_index += 1
                    continue
            self.req_lists[CandidateRequirement.CHALLENGE].append(None)

        exam_req = get_object_or_none(
            ExamFileCandidateRequirement, term=self.current_term)
        self.req_lists[CandidateRequirement.EXAM_FILE].append(exam_req)

        resume_req = get_object_or_none(
            ResumeCandidateRequirement, term=self.current_term)
        self.req_lists[CandidateRequirement.RESUME].append(resume_req)

        manual_reqs = ManualCandidateRequirement.objects.filter(
            term=self.current_term)
        for manual_req in manual_reqs:
            self.req_lists[CandidateRequirement.MANUAL].append(manual_req)

        return super(CandidateRequirementsEditView, self).dispatch(
            *args, **kwargs)

    def get_context_data(self, **kwargs):
        def get_entry(name, req, form):
            """Helper method that returns a dictionary containing a requirement
            name and a form, to be used for each requirement in the template.
            """
            entry = {'requirement': name, 'form': form}
            form.initial['credits_needed'] = 0
            if req:
                form.instance = req
                form.initial['credits_needed'] = req.credits_needed
            return entry

        context = super(CandidateRequirementsEditView, self).get_context_data(
            **kwargs)
        context['term'] = self.current_term
        formset = self.get_form(self.form_class)
        form_index = 0

        # Initialize req_types to contain lists for every requirement type
        req_types = {}
        for req in CandidateRequirement.REQUIREMENT_TYPE_CHOICES:
            req_types[req[0]] = []

        for i, event_type in enumerate(self.event_types):
            req = self.req_lists[CandidateRequirement.EVENT][i]
            form = formset[form_index]
            entry = get_entry(event_type.name, req, form)
            req_types[CandidateRequirement.EVENT].append(entry)
            form_index += 1

        for i, challenge_type in enumerate(self.challenge_types):
            req = self.req_lists[CandidateRequirement.CHALLENGE][i]
            form = formset[form_index]
            entry = get_entry(challenge_type.name, req, form)
            req_types[CandidateRequirement.CHALLENGE].append(entry)
            form_index += 1

        req = self.req_lists[CandidateRequirement.EXAM_FILE][0]
        form = formset[form_index]
        entry = get_entry('', req, form)
        req_types[CandidateRequirement.EXAM_FILE].append(entry)
        form_index += 1

        req = self.req_lists[CandidateRequirement.RESUME][0]
        form = formset[form_index]
        entry = get_entry('', req, form)
        req_types[CandidateRequirement.RESUME].append(entry)
        form_index += 1

        for req in self.req_lists[CandidateRequirement.MANUAL]:
            form = formset[form_index]
            entry = get_entry(req.name, req, form)
            req_types[CandidateRequirement.MANUAL].append(entry)
            form_index += 1

        context['req_types'] = req_types
        return context

    def form_valid(self, form):
        # pylint: disable=R0912
        """Check every form individually in the formset:

        Do nothing if a requirement doesn't exist and credits_needed == 0
        Create a requirement if one doesn't exist and credits_needed != 0
        Edit a requirement if one exists and credits_needed != 0
        Delete a requirement if one exists and credits_needed == 0
        """
        form_index = 0

        for i, event_type in enumerate(self.event_types):
            req = self.req_lists[CandidateRequirement.EVENT][i]
            current_form = form[form_index]
            credits_needed = current_form.cleaned_data.get('credits_needed')
            if credits_needed != 0:
                if req:
                    req.credits_needed = credits_needed
                    req.save()
                else:
                    EventCandidateRequirement.objects.get_or_create(
                        requirement_type=CandidateRequirement.EVENT,
                        credits_needed=credits_needed, term=self.current_term,
                        event_type=event_type)
            else:
                if req:
                    req.delete()
            form_index += 1

        for i, challenge_type in enumerate(self.challenge_types):
            req = self.req_lists[CandidateRequirement.CHALLENGE][i]
            current_form = form[form_index]
            credits_needed = current_form.cleaned_data.get('credits_needed')
            if credits_needed != 0:
                if req:
                    req.credits_needed = credits_needed
                    req.save()
                else:
                    ChallengeCandidateRequirement.objects.get_or_create(
                        requirement_type=CandidateRequirement.CHALLENGE,
                        credits_needed=credits_needed, term=self.current_term,
                        challenge_type=challenge_type)
            else:
                if req:
                    req.delete()
            form_index += 1

        req = self.req_lists[CandidateRequirement.EXAM_FILE][0]
        current_form = form[form_index]
        credits_needed = current_form.cleaned_data.get('credits_needed')
        if credits_needed != 0:
            if req:
                req.credits_needed = credits_needed
                req.save()
            else:
                ExamFileCandidateRequirement.objects.get_or_create(
                    requirement_type=CandidateRequirement.EXAM_FILE,
                    credits_needed=credits_needed, term=self.current_term)
        else:
            if req:
                req.delete()
        form_index += 1

        req = self.req_lists[CandidateRequirement.RESUME][0]
        current_form = form[form_index]
        credits_needed = current_form.cleaned_data.get('credits_needed')
        if credits_needed != 0:
            if req:
                req.credits_needed = credits_needed
                req.save()
            else:
                ResumeCandidateRequirement.objects.get_or_create(
                    requirement_type=CandidateRequirement.RESUME,
                    credits_needed=credits_needed, term=self.current_term)
        else:
            if req:
                req.delete()
        form_index += 1

        for req in self.req_lists[CandidateRequirement.MANUAL]:
            credits_needed = form[form_index].cleaned_data.get('credits_needed')
            if credits_needed != 0:
                req.credits_needed = credits_needed
                req.save()
                form_index += 1
            else:
                req.delete()

        messages.success(self.request, 'Changes saved!')
        return super(CandidateRequirementsEditView, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct your input fields.')
        return super(CandidateRequirementsEditView, self).form_invalid(form)

    def get_success_url(self):
        return reverse('candidates:edit-requirements')


class ManualCandidateRequirementCreateView(CreateView):
    form_class = ManualCandidateRequirementForm
    template_name = 'candidates/add_manual_requirement.html'
    display_req_type = None

    @method_decorator(login_required)
    @method_decorator(permission_required(
        'candidates.add_candidaterequirement', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(ManualCandidateRequirementCreateView, self).dispatch(
            *args, **kwargs)

    def form_valid(self, form):
        """Set the term of the requirement to the current term."""
        form.instance.term = Term.objects.get_current_term()
        messages.success(self.request, '{req_type} requirement created!'.format(
            req_type=self.display_req_type))
        return super(
            ManualCandidateRequirementCreateView, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct your input fields.')
        return super(
            ManualCandidateRequirementCreateView, self).form_invalid(form)

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

        # Initialize req_types to contain lists for every requirement type
        req_types = {}
        for req in CandidateRequirement.REQUIREMENT_TYPE_CHOICES:
            req_types[req[0]] = []

        electives_required = Candidate.are_electives_required(self.candidate)

        for req in requirements:
            req_progress = req.get_progress(self.candidate)
            completed = req_progress['completed']
            credits_needed = req_progress['required']
            if electives_required and completed > credits_needed:
                completed = credits_needed

            entry = {
                'completed': completed,
                'credits_needed': credits_needed,
                'requirement': req
            }
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


class CandidateInitiationView(CandidateListView):
    """View for marking candidates as initiated, granting member status."""
    template_name = 'candidates/initiation.html'

    @method_decorator(login_required)
    @method_decorator(permission_required(
        'candidates.can_initiate_candidates', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(CandidateInitiationView, self).dispatch(*args, **kwargs)

    def get_queryset(self, *args, **kwargs):
        return super(CandidateInitiationView, self).get_queryset(
            *args, **kwargs).select_related('user__userprofile', 'term')


@require_POST
@permission_required('candidates.can_initiate_candidates', raise_exception=True)
def update_candidate_initiation_status(request):
    """Endpoint for updating a candidate's initiation status.

    The post parameters "candidate" and "initiated" specify the candidate (by
    Candidate pk) and their new initiation status, respectively.
    """
    candidate_pk = request.POST.get('candidate')
    if not candidate_pk:
        return json_response(status=404)
    candidate = get_object_or_none(Candidate, pk=candidate_pk)
    initiated = json.loads(request.POST.get('initiated'))
    if not candidate or initiated is None:
        return json_response(status=400)

    candidate.initiated = initiated
    candidate.save(update_fields=['initiated'])
    # TODO(sjdemartini): Update LDAP-related information, like removal from
    # or addition to relevant groups.
    # TODO(sjdemartini): Update relevant mailing lists, moving initiated
    # candidates off of the candidates list and onto the members list.
    return json_response()
