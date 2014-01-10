from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView

from quark.mailing_lists.utils import get_lists


class MailingListsListAllView(ListView):
    context_object_name = 'mailing_lists'
    template_name = 'mailing_lists/list.html'

    @method_decorator(login_required)
    # TODO(giovanni): add officer_required
    def dispatch(self, *args, **kwargs):
        return super(MailingListsListAllView, self).dispatch(
            *args, **kwargs)

    def get_queryset(self, *args, **kwargs):
        return get_lists()
