from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import CreateView
from django.views.generic import DetailView
from django.views.generic import FormView
from django.views.generic import ListView
from django.views.generic import TemplateView
from django.views.generic import UpdateView

from quark.base.models import Term
from quark.base.views import TermParameterMixin
from quark.events.forms import EventForm
from quark.events.forms import EventSignUpAnonymousForm
from quark.events.forms import EventSignUpForm
from quark.events.models import Event
from quark.events.models import EventSignUp
from quark.shortcuts import AjaxResponseMixin


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
        events = Event.objects.get_user_viewable(self.request.user)
        if (not self.is_current or self.show_all or
                show_all_val.lower() == 'true'):
            # Show all events in the display_term if the term is not the
            # current term, or if the show_all parameter is "true"
            self.show_all = True
            events = events.filter(term=self.display_term)
        else:
            # Events from the current term that have not yet ended and have not
            # been cancelled
            events = events.get_upcoming()
        return events.select_related('event_type', 'committee')

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


class EventUpdateView(UpdateView):
    """View for editing a previously-created event."""

    form_class = EventForm
    model = Event
    pk_url_kwarg = 'event_pk'
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


class EventDetailView(DetailView):
    """View for event details and signing up for events."""
    pk_url_kwarg = 'event_pk'
    model = Event
    template_name = 'events/detail.html'
    form = None  # The form can be passed in as a parameter

    def dispatch(self, *args, **kwargs):
        event = self.get_object()
        # If this user can't view the current event, redirect to redirect to
        # login if they aren't already logged in, otherwise raise
        # PermissionDenied
        if not event.can_user_view(self.request.user):
            if self.request.user.is_authenticated():
                raise PermissionDenied
            else:
                return redirect_to_login(self.request.path)
        return super(EventDetailView, self).dispatch(*args, **kwargs)

    def post(self, *args, **kwargs):
        # Enable the view to perform the same action on post as for get
        return self.get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(EventDetailView, self).get_context_data(**kwargs)

        context['signup_list'] = self.object.eventsignup_set.filter(
            unsignup=False).order_by('name').select_related('person')

        signup = None

        if (self.form or not self.object.is_upcoming()
                or not self.object.can_user_sign_up(self.request.user)):
            # If form passed in to view, use that. Or if the event is no longer
            # upcoming or the user isn't allowed to sign up, don't supply a
            # signup form.
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


class EventSignUpView(AjaxResponseMixin, FormView):
    """Handles the form action for signing up for events."""
    # TODO(sjdemartini): Handle various scenarios for failed signups. For
    # instance, no more spots left, not allowed to bring x number of guests,
    # etc.
    event = None  # The event that this sign-up corresponds to

    def dispatch(self, *args, **kwargs):
        self.event = get_object_or_404(Event, pk=self.kwargs['event_pk'])
        # A user cannot sign up unless they have permission to view the event
        if not self.event.can_user_sign_up(self.request.user):
            raise PermissionDenied
        return super(EventSignUpView, self).dispatch(*args, **kwargs)

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

    def get_success_url(self):
        return self.event.get_absolute_url()


class IndividualAttendanceListView(TermParameterMixin, TemplateView):
    template_name = 'events/individual_attendance.html'
    attendance_user = None

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        self.attendance_user = get_object_or_404(
            get_user_model(), username=self.kwargs['username'])
        return super(IndividualAttendanceListView, self).dispatch(
            *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(
            IndividualAttendanceListView, self).get_context_data(**kwargs)
        context['attendance_user'] = self.attendance_user

        # Get non-cancelled events from the given term, and select_related for
        # event_type, since it is used in the template for each event:
        events = Event.objects.get_user_viewable(self.request.user).filter(
            term=self.display_term, cancelled=False).order_by(
            'end_datetime').select_related('event_type')

        current_time = timezone.now()
        past_events = events.filter(end_datetime__lte=current_time)
        future_events = events.filter(end_datetime__gt=current_time)

        context['attended'] = past_events.filter(
            eventattendance__person=self.attendance_user)

        # Get future events that the user has either signed up for or already
        # received attendance for:
        signup_filter = Q(eventsignup__person=self.attendance_user,
                          eventsignup__unsignup=False)
        attendance_filter = Q(eventattendance__person=self.attendance_user)
        participation_filter = signup_filter | attendance_filter
        context['future_participating'] = future_events.filter(
            participation_filter)

        # Get past events that don't have attendance recorded:
        context['past_not_recorded'] = past_events.filter(
            eventattendance__isnull=True)

        # Get past events (that had attendance recorded) that the user did not
        # attend:
        context['not_attended'] = past_events.exclude(
            eventattendance__isnull=True).exclude(pk__in=context['attended'])

        # Get future events for which the user has not signed up or received
        # attendance:
        context['future_not_participating'] = future_events.exclude(
            pk__in=context['future_participating'])

        return context
