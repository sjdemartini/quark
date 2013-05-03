from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import CreateView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView

from quark.base.models import Term
from quark.minutes.forms import InputForm, UploadForm
from quark.minutes.models import Minutes


class MinutesListView(ListView):
    context_object_name = 'minutes'
    template_name = 'minutes/index.html'
    term = None

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        self.term = self.kwargs['term']
        return super(MinutesListView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        return Minutes.objects.filter(term=self.term)

    def get_context_data(self, **kwargs):
        context = super(MinutesListView, self).get_context_data(**kwargs)
        context['terms'] = Term.objects.all()
        context['term_selected'] = self.term
        return context


class MinutesCreateView(CreateView):
    form_class = InputForm
    template_name = 'minutes/add.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(MinutesCreateView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.author = self.request.user
        obj.save()
        return super(MinutesCreateView, self).form_valid(form)


class MinutesDetailView(DetailView):
    context_object_name = 'minutes'
    model = Minutes
    pk_url_kwarg = 'minute_id'
    template_name = 'minutes/detail.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(MinutesDetailView, self).dispatch(*args, **kwargs)


class MinutesEditView(UpdateView):
    form_class = InputForm
    pk_url_kwarg = 'minute_id'
    template_name = 'minutes/edit.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(MinutesEditView, self).dispatch(*args, **kwargs)


class MinutesUploadView(CreateView):
    form_class = UploadForm
    template_name = 'minutes/upload.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(MinutesUploadView, self).dispatch(*args, **kwargs)