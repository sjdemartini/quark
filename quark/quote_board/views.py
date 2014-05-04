from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.core.urlresolvers import reverse
from django.utils.decorators import method_decorator
from django.views.generic import CreateView
from django.views.generic import DetailView
from django.views.generic import ListView

from quark.quote_board.forms import QuoteForm
from quark.quote_board.models import Quote


class QuoteListView(ListView):
    context_object_name = 'quote_list'
    queryset = Quote.objects.select_related(
        'submitter__userprofile').prefetch_related('speakers__userprofile')
    template_name = 'quote_board/list.html'

    @method_decorator(login_required)
    @method_decorator(
        permission_required('quote_board.view_quotes', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(QuoteListView, self).dispatch(*args, **kwargs)


class QuoteDetailView(DetailView):
    context_object_name = 'quote'
    model = Quote
    pk_url_kwarg = 'quote_pk'
    template_name = 'quote_board/detail.html'

    @method_decorator(login_required)
    @method_decorator(
        permission_required('quote_board.view_quotes', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(QuoteDetailView, self).dispatch(*args, **kwargs)


class QuoteCreateView(CreateView):
    form_class = QuoteForm
    template_name = 'quote_board/add.html'

    @method_decorator(login_required)
    @method_decorator(
        permission_required('quote_board.add_quote', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(QuoteCreateView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.submitter = self.request.user
        obj.save()
        return super(QuoteCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('quote-board:list')
