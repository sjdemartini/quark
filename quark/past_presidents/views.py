from django.views.generic import DetailView
from django.views.generic import ListView

from quark.past_presidents.models import PastPresident


class PastPresidentsListView(ListView):
    context_object_name = 'past_presidents'
    model = PastPresident
    template_name = 'past_presidents/list.html'


class PastPresidentsDetailView(DetailView):
    context_object_name = 'president'
    model = PastPresident
    pk_url_kwarg = 'past_president_id'
    template_name = 'past_presidents/detail.html'
