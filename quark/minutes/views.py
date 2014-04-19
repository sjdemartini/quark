from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.core.urlresolvers import reverse
from django.utils.decorators import method_decorator
from django.views.generic import CreateView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView

from quark.base.views import TermParameterMixin
from quark.minutes.forms import InputForm, UploadForm
from quark.minutes.models import Minutes


class MinutesListView(TermParameterMixin, ListView):
    context_object_name = 'minutes'
    template_name = 'minutes/list.html'
    term = None

    @method_decorator(login_required)
    @method_decorator(
        permission_required('minutes.view_minutes', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(MinutesListView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        return Minutes.objects.filter(term=self.display_term)


class MinutesCreateView(CreateView):
    form_class = InputForm
    model = Minutes
    template_name = 'minutes/add.html'

    @method_decorator(login_required)
    @method_decorator(
        permission_required('minutes.add_minutes', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(MinutesCreateView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super(MinutesCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('minutes:detail', kwargs={'minute_id': self.object.id})


class MinutesDetailView(DetailView):
    context_object_name = 'minutes'
    model = Minutes

    pk_url_kwarg = 'minute_id'
    template_name = 'minutes/detail.html'

    @method_decorator(login_required)
    @method_decorator(
        permission_required('minutes.view_minutes', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(MinutesDetailView, self).dispatch(*args, **kwargs)


class MinutesEditView(UpdateView):
    form_class = InputForm
    model = Minutes
    pk_url_kwarg = 'minute_id'
    template_name = 'minutes/edit.html'

    @method_decorator(login_required)
    @method_decorator(
        permission_required('minutes.change_minutes', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(MinutesEditView, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('minutes:detail', kwargs={'minute_id': self.object.id})


class MinutesUploadView(MinutesCreateView):
    form_class = UploadForm
    template_name = 'minutes/upload.html'

    def form_valid(self, form):
        # Read in the uploaded text file
        notes_file = self.request.FILES['notes']
        # Make sure we are reading from the beginning of the file (necessary
        # if upload validation reads file to examine mimetype):
        notes_file.seek(0)
        form.instance.notes = notes_file.read()
        return super(MinutesUploadView, self).form_valid(form)
