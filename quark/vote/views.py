import collections

from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView

from quark.vote.forms import PollForm
from quark.vote.forms import VoteForm
from quark.vote.models import Poll
from quark.vote.models import Vote
from quark.vote.models import VoteReceipt


class PollCreateView(CreateView):
    form_class = PollForm
    template_name = 'vote/create.html'

    @method_decorator(login_required)
    @method_decorator(
        permission_required('vote.add_poll', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(PollCreateView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.creator = self.request.user
        messages.success(self.request, 'Poll created!')
        return super(PollCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('vote:list')


class PollListView(ListView):
    context_object_name = 'polls'
    queryset = Poll.objects.filter(end_datetime__gte=timezone.now())
    template_name = 'vote/list.html'

    @method_decorator(login_required)
    @method_decorator(
        permission_required('vote.add_vote', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(PollListView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(PollListView, self).get_context_data(**kwargs)

        for poll in context['polls']:
            poll.num_votes_cast = VoteReceipt.objects.filter(
                poll=poll, voter=self.request.user).count()

        return context


class VoteCreateView(CreateView):
    form_class = VoteForm
    template_name = 'vote/vote.html'
    poll = None

    @method_decorator(login_required)
    @method_decorator(
        permission_required('vote.add_vote', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        self.poll = get_object_or_404(Poll, pk=self.kwargs['poll_pk'])

        # Only allow the user to access this page if they haven't used
        # their allotted votes yet
        num_user_votes_cast = VoteReceipt.objects.filter(
            poll=self.poll, voter=self.request.user).count()
        if num_user_votes_cast >= self.poll.max_votes_per_user:
            raise PermissionDenied

        return super(VoteCreateView, self).dispatch(*args, **kwargs)

    def get_form_kwargs(self, **kwargs):
        kwargs = super(VoteCreateView, self).get_form_kwargs(**kwargs)
        kwargs['poll'] = self.poll
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(VoteCreateView, self).get_context_data(**kwargs)
        context['poll'] = self.poll
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Vote submitted!')
        return super(VoteCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('vote:list')


class ResultsView(DetailView):
    context_object_name = 'poll'
    model = Poll
    pk_url_kwarg = 'poll_pk'
    template_name = 'vote/results.html'
    object = None

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        self.object = self.get_object()

        # Only allow the creator to view the results of the poll
        if self.request.user != self.object.creator:
            raise PermissionDenied

        return super(ResultsView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ResultsView, self).get_context_data(**kwargs)
        votes = Vote.objects.filter(poll=self.object)
        # Create a dictionary mapping nominee to the reasons for the votes for
        # that person.
        nominee_reasons = collections.defaultdict(list)
        for vote in votes:
            nominee_reasons[vote.nominee].append(vote.reason)
        # Create a list of dictionaries, where each dictionary contains nominee,
        # the reasons for each vote that nominee received, and the percentage of
        # votes a user has received.
        results = []
        total = votes.count()
        for key in nominee_reasons:
            results.append(
                {'nominee': key, 'reasons': nominee_reasons[key],
                 'percentage': float(len(nominee_reasons[key]))/total*100})
        context['results'] = sorted(results,
                                    key=lambda entry: len(entry['reasons']),
                                    reverse=True)
        context['total'] = votes.count()
        return context
