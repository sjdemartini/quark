from pytz import timezone as tz
from datetime import datetime
from datetime import timedelta
import vobject

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.db.models import Count
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET
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
from quark.utils.ajax import AjaxFormResponseMixin
from quark.utils.ajax import json_response


user_model = get_user_model()


class EventListView(TermParameterMixin, ListView):
    """List events in a particular term (display_term from TermParameterMixin).

    The show_all boolean parameter (default false) is taken from a show_all URL
    get request parameter. When true, the queryset includes all events from the
    display_term. Note that the show_all parameter can be passed as a keyword
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
    """View for event details and signing up for events (GET requests)."""
    pk_url_kwarg = 'event_pk'
    model = Event
    template_name = 'events/detail.html'
    object = None  # The event object being fetched for the DetailView

    @method_decorator(require_GET)
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
            if self.request.user.is_authenticated():
                try:
                    signup = EventSignUp.objects.get(
                        event=self.object, user=self.request.user)
                    if signup.unsignup:
                        # If the user has unsigned up, provide a new signup
                        # form
                        context['form'] = EventSignUpForm(self.object)
                    else:
                        context['form'] = EventSignUpForm(
                            self.object, instance=signup)
                except EventSignUp.DoesNotExist:
                    context['form'] = EventSignUpForm(
                        self.object,
                        initial={'name': self.request.user.get_full_name()})
            else:
                context['form'] = EventSignUpAnonymousForm(self.object)

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
    """Handles the form action for signing up for events (POST requests)."""
    # TODO(sjdemartini): Handle various scenarios for failed signups. For
    # instance, no more spots left, not allowed to bring x number of guests,
    # etc.
    event = None  # The event that this sign-up corresponds to
    object = None  # The event signup object

    @method_decorator(require_POST)
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

    def get_form_kwargs(self, **kwargs):
        """Set the event and the user in the form."""
        kwargs = super(EventSignUpView, self).get_form_kwargs(**kwargs)
        kwargs['event'] = self.event
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Check whether the signup was created or updated."""
        self.object = form.save(commit=False)
        created = self.object.pk is None
        self.object.save()

        if created:
            msg = 'Signup successful!'
        else:
            msg = 'Signup updated!'

        messages.success(self.request, msg)
        return self.render_to_json_response()

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


class AttendanceRecordView(DetailView):
    """View for recording attendance for a given event."""
    model = Event
    context_object_name = 'event'
    pk_url_kwarg = 'event_pk'
    template_name = 'events/attendance.html'

    @method_decorator(login_required)
    @method_decorator(
        permission_required('events.add_eventattendance', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(AttendanceRecordView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(AttendanceRecordView, self).get_context_data(**kwargs)
        current_term = Term.objects.get_current_term()

        officers = user_model.objects.filter(
            officer__term=current_term).select_related(
            'userprofile').order_by('userprofile').distinct()
        context['officers'] = officers

        candidates = user_model.objects.filter(
            candidate__term=current_term).select_related(
            'userprofile').order_by('userprofile').distinct()
        context['candidates'] = candidates

        # Get all other users (not including officers or candidates) who either
        # signed up or received attendance for this event:
        context['members'] = user_model.objects.filter(
            Q(eventsignup__event=self.object, eventsignup__unsignup=False) |
            Q(eventattendance__event=self.object)).distinct().exclude(
            Q(pk__in=officers) | Q(pk__in=candidates)).select_related(
            'userprofile').order_by('userprofile')

        # Create a set of the pk's of attendees', useful for checking (in
        # constant time) whether a given user is an attendee:
        context['attendees'] = set(user_model.objects.filter(
            eventattendance__event=self.object).values_list('pk', flat=True))

        # Similarly create a set of the pk's of people who have signed up:
        context['signed_up'] = set(user_model.objects.filter(
            eventsignup__event=self.object,
            eventsignup__unsignup=False).values_list('pk', flat=True))

        return context


@require_POST
@permission_required('events.add_eventattendance', raise_exception=True)
def attendance_submit(request):
    """Record attendance for a given user at a given event.

    The user is specified by a userPK post parameter, and the event is
    specified by an eventPK post parameter.
    """
    event_pk = request.POST['eventPK']
    event = Event.objects.get(pk=event_pk)
    user_pk = request.POST['userPK']
    user = user_model.objects.get(pk=user_pk)
    # Record attendance for this user at this event
    EventAttendance.objects.get_or_create(user=user, event=event)
    return json_response()


@require_POST
@permission_required('events.delete_eventattendance', raise_exception=True)
def attendance_delete(request):
    """Remove attendance for a given user at a given event.

    The user is specified by a userPK post parameter, and the event is
    specified by an eventPK post parameter.
    """
    event_pk = request.POST['eventPK']
    event = Event.objects.get(pk=event_pk)
    user_pk = request.POST['userPK']
    # Delete this user's attendance for the event if it exists:
    try:
        EventAttendance.objects.get(user__pk=user_pk, event=event).delete()
    except EventAttendance.DoesNotExist:
        # Fine if the attendance does not exist, since we wanted to remove it
        pass
    return json_response()


def attendance_search(request, max_results=20):
    """Return a JSON response of members based on search for name.

    The search uses the "searchTerm" post parameter. Return up to max_results
    number of results. The results only include people who have not attended
    the event specified by the post parameter eventPK.
    """
    search_query = request.GET['searchTerm']
    event_pk = request.GET['eventPK']
    event = Event.objects.get(pk=event_pk)

    # Get all users who did not attend this event:
    # TODO(sjdemartini): Properly filter for members, instead of just getting
    # all users who are not officers or candidates (as these other users may
    # include company users, etc.)
    members = user_model.objects.exclude(
        eventattendance__event=event).select_related(
        'userprofile')

    # A list of entries for each member that matches the search query:
    member_matches = []

    # Parse the search query into separate pieces if the query includes
    # whitespace
    search_terms = search_query.lower().split()
    for member in members:
        name = member.userprofile.get_verbose_full_name()
        name_lower = name.lower()
        if all(search_term in name_lower for search_term in search_terms):
            entry = {
                'label': name,
                'value': member.pk
            }
            member_matches.append(entry)
        if len(member_matches) >= max_results:
            break
    return json_response(data=member_matches)


class IndividualAttendanceListView(TermParameterMixin, TemplateView):
    template_name = 'events/individual_attendance.html'
    attendance_user = None

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        self.attendance_user = get_object_or_404(
            user_model, username=self.kwargs['username'])
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
    paginate_by = 75
    template_name = 'events/leaderboard.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LeaderboardListView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        leaders = get_user_model().objects.filter(
            eventattendance__event__term=self.display_term,
            eventattendance__event__cancelled=False).select_related(
            'userprofile').annotate(count=Count('eventattendance')).order_by(
            '-count')

        if len(leaders) > 0:
            max_events = leaders[0].count or 0
        else:
            max_events = 0

        # Create a list of "leader" entries, where each entry is a dictionary
        # that includes the user, their rank on the leaderboard (1st, 2nd,
        # etc.), and their leaderboard width "factor" (see below for details).
        leader_list = []
        if max_events > 0:  # make sure there's no divide by zero
            prev_value = -1
            prev_rank = 1

            for i, leader in enumerate(leaders, start=prev_rank):
                # factor used for CSS width property (percentage). Use 70 as
                # the max width (i.e. the user who attended the most events has
                # width 70%), including adding 2.5 to every factor to make sure
                # that there is enough room for text to be displayed.
                factor = 2.5 + leader.count * 67.5 / max_events
                if leader.count == prev_value:
                    rank = prev_rank
                else:
                    rank = i
                prev_rank = rank
                prev_value = leader.count

                # Add the leader entry to the list
                leader_list.append({'user': leader,
                                    'factor': factor,
                                    'rank': rank})
        return leader_list


def ical(request, event_pk=None):
    """Return an ICS file for the given event,
    or for all events if no event specified.

    If a "term" URL parameter is given and no event is provided,
    the view returns all events for that term
    """
    cal = vobject.iCalendar()

    cal.add('calscale').value = 'Gregorian'
    cal.add('X-WR-TIMEZONE').value = 'America/Los_Angeles'
    cal.add('X-WR-CALNAME').value = 'TBP Events'
    cal.add('X-WR-CALDESC').value = 'TBP Events'

    vtimezone = cal.add('vtimezone')
    vtimezone.add('tzid').value = "America/Los_Angeles"
    vtimezone.add('X-LIC-LOCATION').value = "America/Los_Angeles"
    dst = vtimezone.add('daylight')
    dst.add('tzoffsetfrom').value = '-0800'
    dst.add('tzoffsetto').value = '-0700'
    dst.add('tzname').value = 'PDT'
    dst.add('dtstart').value = datetime(
        1970, 3, 8, 2, 0, 0, 0, tz('US/Pacific'))  # '19700308T020000'
    dst.add('rrule').value = 'FREQ=YEARLY;BYMONTH=3;BYDAY=2SU'
    std = vtimezone.add('standard')
    std.add('tzoffsetfrom').value = '-0700'
    std.add('tzoffsetto').value = '-0800'
    std.add('tzname').value = 'PST'
    std.add('dtstart').value = datetime(
        1970, 11, 1, 2, 0, 0, 0, tz('US/Pacific'))  # '19701101T020000'
    std.add('rrule').value = 'FREQ=YEARLY;BYMONTH=11;BYDAY=1SU'

    # TODO(giovanni): Add user authorization
    if event_pk is None:    # i.e., if we want all events
        filename = 'events.ics'
        term = request.GET.get('term', '')
        events = Event.objects.get_user_viewable(
            request.user).filter(cancelled=False)
        if term:
            term_obj = Term.objects.get_by_url_name(term)
            events = events.filter(term=term_obj)
        for event in events:
            add_event_to_ical(event, cal)
    else:    # i.e., we want a specific event
        filename = 'event.ics'
        event = Event.objects.get(pk=event_pk)
        add_event_to_ical(event, cal)

    response = HttpResponse(cal.serialize(), mimetype='text/calendar')
    response['Filename'] = filename  # IE needs this
    response['Content-Disposition'] = 'attachment; filename=' + filename
    return response


def add_event_to_ical(event, cal):
    """Helper method used by the ical methods.

    Takes in event and cal where:
    event is the actual event object
    cal is the ical object
    """
    ical_event = cal.add('vevent')
    name = event.name
    if event.restriction == Event.MEMBER:
        name += " (Members Only)"
    elif event.restriction == Event.OFFICER:
        name += " (Officers Only)"
    ical_event.add('summary').value = name
    ical_event.add('location').value = event.location
    event_url = 'https://{}{}'.format(settings.HOSTNAME,
                                      event.get_absolute_url())
    if event.description:
        description = u'{}\n\n{}'.format(event.description,
                                         event_url)
    else:
        description = event_url
    ical_event.add('description').value = description
    ical_event.add('dtstart').value = event.start_datetime
    ical_event.add('dtend').value = event.end_datetime
    ical_event.add('uid').value = str(event.id)
