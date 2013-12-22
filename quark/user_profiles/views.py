from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import UpdateView

from quark.user_profiles.forms import UserProfileForm


class UserProfileEditView(UpdateView):
    form_class = UserProfileForm
    success_url = reverse_lazy('user-profiles:edit')
    template_name = 'user_profiles/edit.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UserProfileEditView, self).dispatch(*args, **kwargs)

    def get_object(self, *args, **kwargs):
        return self.request.user.userprofile

    def form_valid(self, form):
        messages.success(self.request, 'Changes saved!')
        return super(UserProfileEditView, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct your input fields.')
        return super(UserProfileEditView, self).form_invalid(form)
