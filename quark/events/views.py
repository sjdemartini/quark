from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.core.urlresolvers import reverse
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import CreateView
from django.views.generic import DetailView
from django.views.generic import FormView
from django.views.generic import ListView
from django.views.generic import UpdateView

from quark.base.models import Term
from quark.events.forms import EventForm
from quark.events.forms import EventSignUpAnonymousForm
from quark.events.forms import EventSignUpForm
from quark.events.models import Event
from quark.events.models import EventAttendance
from quark.events.models import EventSignUp
from quark.base.views import TermParameterMixin


class EventListView(TermParameterMixin, ListView):
    """List events in a particular term (display_term from TermParameterMixin).

    The show_all boolean parameter (default false) is taken from a show_all URL
    get request parameter. When true, the queryset includes all events from the
    display_term. Note that the show_all paramater can be passed as a keyword
    argument to the view in the as_view() method.
    """
    context_object_name = 'events'
    template_name = 'events/list.html'
    show_all = False

    def get_queryset(self):
        show_all_val = self.request.GET.get('show_all', '')
        if (not self.is_current or self.show_all or
                show_all_val.lower() == 'true'):
            # Show all events in the display_term if the term is not the
            # current term, or if the show_all parameter is "true"
            self.show_all = True
            events = Event.objects.filter(term=self.display_term)
        else:
            # Events from the current term that have not yet ended and have not
            # been cancelled
            events = Event.objects.get_upcoming()
        return events

    def get_context_data(self, **kwargs):
        context = super(EventListView, self).get_context_data(**kwargs)
        context['show_all'] = self.show_all
        return context


class EventCreateView(CreateView):
    """View for adding new events."""
    form_class = EventForm
    template_name = 'events/add.html'

    @method_decorator(login_required)
    @method_decorator(
        permission_required('events.add_event', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(EventCreateView, self).dispatch(*args, **kwargs)

    def get_initial(self):
        start_time = timezone.now().replace(minute=0, second=0)
        end_time = start_time + timedelta(hours=1)
        current_term = Term.objects.get_current_term()
        return {'start_datetime': start_time,
                'end_datetime': end_time,
                'term': current_term.id if current_term else None,
                'contact': self.request.user,  # usable since login_required
                'needs_pr': True}

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct your input fields.')
        return super(EventCreateView, self).form_invalid(form)

    def form_valid(self, form):
        messages.success(self.request, 'Event Successfully Created!')
        return super(EventCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('events:detail', args=(self.object.id,))


class EventUpdateView(UpdateView):
    """View for editing a previously-created event."""

    form_class = EventForm
    model = Event
    pk_url_kwarg = 'event_id'
    template_name = 'events/edit.html'

    @method_decorator(login_required)
    @method_decorator(
        permission_required('events.change_event', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(EventUpdateView, self).dispatch(*args, **kwargs)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct your input fields.')
        return super(EventUpdateView, self).form_invalid(form)

    def form_valid(self, form):
        messages.success(self.request, 'Event Successfully Updated!')
        return super(EventUpdateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('events:detail', args=(self.object.id,))


class EventDetailView(DetailView):
    """View for event details and signing up for events."""
    # TODO(sjdemartini): Handle event permissions (who can see which events)

    pk_url_kwarg = 'event_id'
    model = Event
    template_name = 'events/detail.html'
    form = None  # The form can be passed in as a parameter

    def post(self, *args, **kwargs):
        # Enable the view to perform the same action on post as for get
        return self.get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(EventDetailView, self).get_context_data(**kwargs)

        context['signup_list'] = self.object.eventsignup_set.filter(
            unsignup=False).order_by('name')

        signup = None

        if self.form or not self.object.is_upcoming():
            # If form passed in to view, use that. Or if the event is no longer
            # upcoming, don't supply a signup form.
            context['form'] = self.form
        else:
            max_guests = self.object.max_guests_per_person
            if self.request.user.is_authenticated():
                try:
                    signup = EventSignUp.objects.get(
                        event=self.object, person=self.request.user)
                    context['form'] = EventSignUpForm(instance=signup,
                                                      max_guests=max_guests)
                except EventSignUp.DoesNotExist:
                    context['form'] = EventSignUpForm(
                        initial={'name': self.request.user.get_full_name()},
                        max_guests=max_guests)
            else:
                context['form'] = EventSignUpAnonymousForm(
                    max_guests=max_guests)

        context['user_signed_up'] = signup is not None and not signup.unsignup

        context['num_signups'] = len(context['signup_list'])
        context['num_guests'] = self.object.get_num_guests()
        total_rsvps = context['num_signups'] + context['num_guests']

        context['total_seats'] = context['signup_list'].aggregate(
            Sum('driving'))['driving__sum'] or 0

        context['available_seats'] = context['total_seats'] - total_rsvps

        return context


class EventSignUpView(FormView):
    """Handles the form action for signing up for events."""
    # TODO(sjdemartini): Handle various scenarios for failed signups. For
    # instance, no more spots left, not allowed to bring x number of guests,
    # etc.
    event = None  # The event that this sign-up corresponds to

    def dispatch(self, *args, **kwargs):
        self.event = get_object_or_404(Event, id=self.kwargs['event_id'])
        return super(EventSignUpView, self).dispatch(*args, **kwargs)

    def get(self, *args, **kwargs):
        return redirect(self.get_success_url())

    def get_form_class(self):
        if self.request.user.is_authenticated():
            return EventSignUpForm
        else:
            return EventSignUpAnonymousForm

    def get_form(self, *args, **kwargs):
        form = super(EventSignUpView, self).get_form(*args, **kwargs)
        form.instance.event = self.event
        return form

    def get_form_kwargs(self, **kwargs):
        """Set the number of max guests in the form."""
        kwargs = super(EventSignUpView, self).get_form_kwargs(**kwargs)
        kwargs['max_guests'] = self.event.max_guests_per_person
        return kwargs

    def form_valid(self, form):
        """Only save a new object if a signup does not already exist for this
        user. Otherwise, just update the existing object.
        """
        # Get the form instance, not yet saved to the database:
        obj = form.save(commit=False)

        if self.request.user.is_authenticated():
            signup, created = EventSignUp.objects.get_or_create(
                event=self.event, person=self.request.user)
            signup.person = self.request.user
        else:
            signup, created = EventSignUp.objects.get_or_create(
                event=self.event, email=obj.email)

        # Copy over values from form instance to signup object in database:
        signup.name = obj.name
        signup.num_guests = obj.num_guests
        signup.driving = obj.driving
        signup.comments = obj.comments
        signup.email = obj.email
        signup.unsignup = False
        signup.save()

        if created:
            msg = 'Signup successful!'
        else:
            msg = 'Signup updated!'

        messages.success(self.request, msg)
        return super(EventSignUpView, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Signup unsuccessful.')
        view = EventDetailView.as_view(form=form)
        return view(self.request, **self.kwargs)

    def get_success_url(self):
        return reverse('events:detail', args=(self.event.id,))


class IndividualAttendanceListView(ListView):
    context_object_name = 'attendances'
    model = EventAttendance
    template_name = 'events/individual_attendance.html'
    term = None

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        self.term = Term.objects.get_current_term()
        return super(IndividualAttendanceListView, self).dispatch(
            *args, **kwargs)

    def get_queryset(self):
        return EventAttendance.objects.filter(
            event__term=self.term,
            person=self.request.user).order_by(
            'event__end_datetime')

    def get_context_data(self, **kwargs):
        context = super(
            IndividualAttendanceListView, self).get_context_data(**kwargs)
        context['signups'] = EventSignUp.objects.filter(
            person=self.request.user, unsignup=False)
        context['display_term'] = self.term
        return context
