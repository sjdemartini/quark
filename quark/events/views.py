from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.db.models import Count
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
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
from quark.events.models import EventAttendance
from quark.events.models import EventSignUp
from quark.shortcuts import get_object_or_none
from quark.utils.ajax import AjaxFormResponseMixin
from quark.utils.ajax import json_response


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
    object = None  # The event object being fetched for the DetailView

    def dispatch(self, *args, **kwargs):
        self.object = self.get_object()
        # If this user can't view the current event, redirect to login if they
        # aren't already logged in; otherwise raise PermissionDenied
        if not self.object.can_user_view(self.request.user):
            if self.request.user.is_authenticated():
                raise PermissionDenied
            else:
                return redirect_to_login(self.request.path)
        return super(EventDetailView, self).dispatch(*args, **kwargs)

    def get_object(self, *args, **kwargs):
        """Return the event object for the detail view.

        Use the cached copy of the object if it exists, otherwise call the
        superclass method. This is useful because get_object is called early
        by the dispatch method.
        """
        return self.object or super(EventDetailView, self).get_object(
            *args, **kwargs)

    def post(self, *args, **kwargs):
        # Enable the view to perform the same action on post as for get
        return self.get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(EventDetailView, self).get_context_data(**kwargs)

        context['signup_list'] = self.object.eventsignup_set.filter(
            unsignup=False).select_related('user', 'user__userprofile')

        signup = None

        if (not self.object.is_upcoming()
                or not self.object.can_user_sign_up(self.request.user)):
            # If the event is no longer upcoming or the user isn't allowed to
            # sign up, don't supply a signup form.
            context['form'] = None
        else:
            extra_kwargs = {'max_guests': self.object.max_guests_per_person,
                            'needs_drivers': self.object.needs_drivers}
            if self.request.user.is_authenticated():
                try:
                    signup = EventSignUp.objects.get(
                        event=self.object, user=self.request.user)
                    if signup.unsignup:
                        # If the user has unsigned up, provide a new signup
                        # form
                        context['form'] = EventSignUpForm(**extra_kwargs)
                    else:
                        context['form'] = EventSignUpForm(
                            instance=signup, **extra_kwargs)
                except EventSignUp.DoesNotExist:
                    context['form'] = EventSignUpForm(
                        initial={'name': self.request.user.get_full_name()},
                        **extra_kwargs)
            else:
                context['form'] = EventSignUpAnonymousForm(**extra_kwargs)

        context['user_signed_up'] = signup is not None and not signup.unsignup

        context['num_signups'] = len(context['signup_list'])
        context['num_guests'] = self.object.get_num_guests()
        total_rsvps = context['num_signups'] + context['num_guests']

        context['total_seats'] = context['signup_list'].aggregate(
            Sum('driving'))['driving__sum'] or 0

        context['available_seats'] = context['total_seats'] - total_rsvps

        def signup_sort_key(signup):
            if signup.user:
                return signup.user.userprofile.get_common_name()
            else:
                return signup.name

        # Sort the signup list using the user's common name or the name used
        # in signup (if anonymous signup)
        context['signup_list'] = sorted(context['signup_list'],
                                        key=signup_sort_key)
        return context


class EventSignUpView(AjaxFormResponseMixin, FormView):
    """Handles the form action for signing up for events."""
    # TODO(sjdemartini): Handle various scenarios for failed signups. For
    # instance, no more spots left, not allowed to bring x number of guests,
    # etc.
    event = None  # The event that this sign-up corresponds to

    def dispatch(self, *args, **kwargs):
        self.event = get_object_or_404(Event, pk=self.kwargs['event_pk'])
        # A user cannot sign up unless they have permission to do so
        if not self.event.can_user_sign_up(self.request.user):
            return json_response(status=403)
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
        kwargs['needs_drivers'] = self.event.needs_drivers
        return kwargs

    def form_valid(self, form):
        """Only save a new object if a signup does not already exist for this
        user. Otherwise, just update the existing object.
        """
        # Get the form instance, not yet saved to the database:
        obj = form.save(commit=False)

        if self.request.user.is_authenticated():
            signup, created = EventSignUp.objects.get_or_create(
                event=self.event, user=self.request.user)
            signup.user = self.request.user
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


@require_POST
def event_unsignup(request, event_pk):
    """Handles the action of un-signing up for events."""
    try:
        event = Event.objects.get(pk=event_pk)
    except:
        return json_response(status=400)
    success_msg = 'Unsignup successful.'
    if request.user.is_authenticated():
        try:
            # Try to get a signup object for this user
            signup = EventSignUp.objects.get(event=event, user=request.user)
            signup.user = request.user

            # Set the signup as "unsigned up"
            signup.unsignup = True
            signup.save()

            messages.success(request, success_msg)
        except EventSignUp.DoesNotExist:
            # If a signup could not be found, ignore this, since the user
            # is not signed up for the event
            pass
    else:
        email = request.POST.get('email')
        if email:
            try:
                signup = EventSignUp.objects.get(event=event, email=email)
                signup.unsignup = True
                signup.save()
                messages.success(request, success_msg)
            except:
                errors = {'email': ('The email address you entered was not '
                                    'used to sign up.')}
                return json_response(status=400, data=errors)
        else:
            errors = {
                'email': 'Please enter the email address you used to sign up.'
            }
            return json_response(status=400, data=errors)
    return json_response()


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
            eventattendance__user=self.attendance_user)

        # Get future events that the user has either signed up for or already
        # received attendance for:
        signup_filter = Q(eventsignup__user=self.attendance_user,
                          eventsignup__unsignup=False)
        attendance_filter = Q(eventattendance__user=self.attendance_user)
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


class LeaderboardListView(TermParameterMixin, ListView):
    """View for selecting all users who have attended an event in a
    particular term (display_term from TermParameterMixin).

    The view omits all users with no attendance.
    """
    context_object_name = 'leader_list'
    template_name = 'events/leaderboard.html'
    paginate_by = 75  # separates leaders into pages of 25 each

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LeaderboardListView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        aggregates = EventAttendance.objects.filter(
            event__term=self.display_term,
            event__cancelled=False).values('user').annotate(
            Count('user')).order_by('-user__count').select_related(
            'user__userprofile')

        if len(aggregates) > 0:
            max_events = aggregates[0]['user__count'] or 0
        else:
            max_events = 0

        leaders = []
        if max_events > 0:  # make sure there's no divide by zero
            i = 0
            prev_value = -1
            prev_rank = 0
        user_model = get_user_model()
        for aggregate in aggregates:
            factor = 2.5 + aggregate['user__count'] * 67.5 / max_events
            # Factor used for CSS width property (percentage).
            # Use 70 as the max width (i.e. the user who attended the most
            # events has width 70%), and add 2.5 to make sure there is enough
            # room to be displayed.
            user = get_object_or_none(user_model, pk=aggregate['user'])
            if user is None:
                continue
            i += 1
            if aggregate['user__count'] != prev_value:
                rank = i
            else:
                rank = prev_rank
            prev_rank = rank
            prev_value = aggregate['user__count']

            leaders.append({'user': user,
                            'count': aggregate['user__count'],
                            'factor': factor,
                            'rank': rank})

        return leaders
