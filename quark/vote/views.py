from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView

from quark.vote.forms import PollForm
from quark.vote.forms import VoteForm
from quark.vote.models import Poll


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


class VoteCreateView(CreateView):
    form_class = VoteForm
    context_object_name = 'poll'
    template_name = 'vote/vote.html'
    poll = None

    @method_decorator(login_required)
    @method_decorator(
        permission_required('vote.add_vote', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        self.poll = get_object_or_404(Poll, pk=self.kwargs['poll_pk'])
        return super(VoteCreateView, self).dispatch(*args, **kwargs)

    def get_form_kwargs(self, **kwargs):
        kwargs = super(VoteCreateView, self).get_form_kwargs(**kwargs)
        kwargs['poll'] = self.poll
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
