from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator
from django.views.generic.edit import CreateView

from quark.vote.forms import PollForm


class PollCreate(CreateView):
    form_class = PollForm
    template_name = "vote/create.html"

    @method_decorator(login_required)
    @method_decorator(
        permission_required('vote.add_poll', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(PollCreate, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.creator = self.request.user
        return super(PollCreate, self).form_valid(form)

    def get_success_url(self):
        messages.success(self.request, 'Poll created!')
        return reverse('home')

# TODO(jerrycheng): complete views for voting and checking results
# class Vote(CreateView):
#     form_class = VoteForm
#     template_name = "vote/vote.html"
#
#     @method_decorator(login_required)
#     @method_decorator(
#         permission_required('vote.add_vote', raise_exception=True))
#     def dispatch(self, *args, **kwargs):
#        return super(Vote, self).dispatch(*args, **kwargs)
