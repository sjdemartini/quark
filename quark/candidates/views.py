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
from django.views.generic.edit import FormView

from quark.base.models import Term
from quark.candidates.models import Candidate
from quark.candidates.models import CandidateRequirement
from quark.candidates.models import CandidateRequirementProgress
from quark.candidates.models import Challenge
from quark.candidates.forms import CandidateRequirementProgressFormSet
from quark.candidates.forms import CandidateRequirementFormSet
from quark.candidates.forms import ChallengeCandidateRequirementForm
from quark.candidates.forms import ChallengeVerifyForm
from quark.candidates.forms import EventCandidateRequirementForm
from quark.candidates.forms import ExamFileCandidateRequirementForm
from quark.candidates.forms import ManualCandidateRequirementForm
from quark.exams.models import Exam


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


class CandidateEditView(FormView):
    form_class = CandidateRequirementProgressFormSet
    template_name = 'candidates/edit.html'
    candidate = None

    @method_decorator(login_required)
    @method_decorator(permission_required(
        'candidates.change_candidate', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        self.candidate = get_object_or_404(
            Candidate, pk=self.kwargs['candidate_pk'])
        return super(CandidateEditView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CandidateEditView, self).get_context_data(**kwargs)
        context['exams'] = Exam.objects.get_approved().filter(
            submitter=self.candidate.user)
        context['challenges'] = Challenge.objects.filter(
            candidate=self.candidate)

        requirements = CandidateRequirement.objects.filter(
            term=Term.objects.get_current_term())
        # Order progresses by requirement so they have the same order as
        # requirements
        progresses = CandidateRequirementProgress.objects.filter(
            candidate=self.candidate).order_by('requirement')

        formset = self.form_class()
        context['candidate'] = self.candidate
        progress_index = 0

        # Initialize requirement_types to contain lists for every
        # requirement type
        requirement_types = {}
        for req in CandidateRequirement.REQUIREMENT_TYPE_CHOICES:
            requirement_types[req[0]] = []

        for i in range(0, requirements.count()):
            entry = {
                'requirement': requirements[i],
                'completed': requirements[i].get_progress(self.candidate)[0],
                'form': formset[i],
                'progress': None}
            formset[i].initial = {
                'manually_recorded_credits': 0,
                'credits_needed': requirements[i].credits_needed,
                'comments': ''}

            # Progresses are ordered the same way as requirements,
            # so all progresses will be correctly checked in the loop
            if progress_index < progresses.count():
                current_progress = progresses[progress_index]
                if current_progress.requirement == requirements[i]:
                    entry['progress'] = current_progress
                    # Set the initial values of the form to the progress
                    formset[i].initial = {
                        'manually_recorded_credits': (
                            current_progress.manually_recorded_credits),
                        'credits_needed': current_progress.
                        alternate_credits_needed,
                        'comments': current_progress.comments}
                    progress_index += 1
            req_type = requirements[i].requirement_type
            requirement_types[req_type].append(entry)

        context['requirement_types'] = requirement_types
        return context

    def form_valid(self, form):
        """Check every form individually in the formset, and create or edit
        progresses if necessary.
        """
        context = self.get_context_data()
        req_types = context['requirement_types']
        form_index = 0

        for entries in req_types.values():
            for entry in entries:
                progress = entry['progress']
                requirement = entry['requirement']
                current_form = form[form_index]

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
                form_index += 1

        messages.success(self.request, 'Changes saved successfully!')
        return super(CandidateEditView, self).form_valid(form)

    def form_invalid(self, form):
        """Add errors to the context so they can be displayed next to each form
        in the template.
        """
        context = self.get_context_data(form=form)
        req_types = context['requirement_types']
        form_index = 0

        for entries in req_types.values():
            for entry in entries:
                try:
                    entry['errors'] = form.errors[
                        form_index]['credits_needed']
                except KeyError:
                    pass  # no errors
                form_index += 1

        messages.error(self.request, 'Please correct your input fields.')
        return self.render_to_response(context)

    def get_success_url(self):
        return reverse(
            'candidates:edit', kwargs={'candidate_pk': self.candidate.pk})


class ChallengeVerifyView(UpdateView):
    context_object_name = 'verify'
    form_class = ChallengeVerifyForm
    model = Challenge
    pk_url_kwarg = 'challenge_pk'
    template_name = 'candidates/verify.html'

    @method_decorator(login_required)
    @method_decorator(permission_required(
        'candidates.change_challenge', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(ChallengeVerifyView, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('candidates:edit',
                       kwargs={'candidate_pk': self.object.candidate.pk})


class CandidateRequirementsEditView(FormView):
    form_class = CandidateRequirementFormSet
    template_name = 'candidates/edit_requirements.html'

    @method_decorator(login_required)
    @method_decorator(permission_required(
        'candidates.change_candidaterequirement', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(CandidateRequirementsEditView, self).dispatch(
            *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CandidateRequirementsEditView, self).get_context_data(
            **kwargs)

        requirements = CandidateRequirement.objects.filter(
            term=Term.objects.get_current_term())
        formset = self.form_class()

        # Initialize requirement_types to contain lists for every
        # requirement type
        requirement_types = {}
        for req in CandidateRequirement.REQUIREMENT_TYPE_CHOICES:
            requirement_types[req[0]] = []

        for i in range(0, requirements.count()):
            entry = {'requirement': requirements[i], 'form': formset[i]}
            formset[i].initial = {
                'credits_needed': requirements[i].credits_needed}
            req_type = requirements[i].requirement_type
            requirement_types[req_type].append(entry)

        context['requirement_types'] = requirement_types
        return context

    def form_valid(self, form):
        """Check every form individually in the formset."""
        context = self.get_context_data()
        req_types = context['requirement_types']
        form_index = 0

        for entries in req_types.values():
            for entry in entries:
                requirement = entry['requirement']
                credits_needed = form[
                    form_index].cleaned_data.get('credits_needed')
                requirement.credits_needed = credits_needed
                requirement.save()
                form_index += 1

        messages.success(self.request, 'Changes saved successfully!')
        return super(CandidateRequirementsEditView, self).form_valid(form)

    def form_invalid(self, form):
        """Add errors to the context so they can be displayed next to each form
        in the template.
        """
        context = self.get_context_data(form=form)
        req_types = context['requirement_types']
        form_index = 0

        for entries in req_types.values():
            for entry in entries:
                try:
                    entry['errors'] = form.errors[
                        form_index]['credits_needed']
                except KeyError:
                    pass  # no errors
                form_index += 1

        messages.error(self.request, 'Please correct your input fields.')
        return self.render_to_response(context)

    def get_success_url(self):
        return reverse('candidates:edit-requirements')


class CandidateRequirementCreateView(CreateView):
    template_name = 'candidates/add_requirement.html'
    requirement_type = None

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
            return EventCandidateRequirementForm
        elif self.requirement_type == CandidateRequirement.CHALLENGE:
            return ChallengeCandidateRequirementForm
        elif self.requirement_type == CandidateRequirement.EXAM_FILE:
            return ExamFileCandidateRequirementForm
        elif self.requirement_type == CandidateRequirement.MANUAL:
            return ManualCandidateRequirementForm
        else:
            raise Http404

    def form_valid(self, form):
        """Set the term of the requirement to the current term."""
        form.instance.term = Term.objects.get_current_term()
        return super(CandidateRequirementCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('candidates:requirement-list')


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

    def get_success_url(self):
        return reverse('candidates:requirement-list')
