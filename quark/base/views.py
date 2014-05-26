from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.views.generic.base import TemplateView

from quark.base.models import Officer
from quark.base.models import Term
from quark.events.models import Event
from quark.newsreel.models import News


class HomePageView(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super(HomePageView, self).get_context_data(**kwargs)
        context['event_list'] = Event.objects.get_user_viewable(
            self.request.user).get_upcoming()[:3]
        context['news_list'] = News.objects.all()[:5]
        return context


class OfficerPortalView(TemplateView):
    template_name = 'base/officer_portal.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        if not self.request.user.userprofile.is_officer():
            raise PermissionDenied
        return super(OfficerPortalView, self).dispatch(*args, **kwargs)


class ITToolsView(TemplateView):
    template_name = 'base/it_tools.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        is_staff = self.request.user.is_staff
        is_superuser = self.request.user.is_superuser
        if not is_staff and not is_superuser:
            raise PermissionDenied
        return super(ITToolsView, self).dispatch(*args, **kwargs)


class ProcrastinationView(TemplateView):
    template_name = 'base/procrastination.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProcrastinationView, self).dispatch(*args, **kwargs)


class TermParameterMixin(object):
    """View mixin that adds a 'display_term' variable to the view class and
    term variables to the context data.

    The display_term is pulled from a "term" URL get request parameter, where
    the term is specified in URL-friendly form (for instance, term=sp2012 for
    Spring 2012). If there is no term parameter, display_term is set to the
    current term. If the term parameter is invalid, the server returns a 400
    error response.

    Also adds an is_current field to the view, which is True if display_term
    is the current term.

    Recommended use with a template that includes "term-selection.html".
    """
    display_term = None  # The Term that the view is displaying/featuring
    is_current = False  # True if display_term is the current term

    def dispatch(self, request, *args, **kwargs):
        term = request.GET.get('term', '')
        current_term = Term.objects.get_current_term()
        if not term:
            self.display_term = current_term
        else:
            self.display_term = Term.objects.get_by_url_name(term)
            if self.display_term is None:
                # Bad request, since their term URL parameter doesn't match a
                # term of ours
                return render(request, template_name='400.html', status=400)

        if self.display_term.pk == current_term.pk:
            self.is_current = True

        return super(TermParameterMixin, self).dispatch(
            request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TermParameterMixin, self).get_context_data(**kwargs)
        context['display_term'] = self.display_term
        context['display_term_name'] = self.display_term.verbose_name()
        context['display_term_url_name'] = self.display_term.get_url_name()
        context['is_current'] = self.is_current

        # Add queryset of all Terms up to and including the current term,
        # ordered from current to oldest
        context['terms'] = Term.objects.get_terms(reverse=True)
        return context


class OfficersListView(TermParameterMixin, ListView):
    context_object_name = 'officers'
    model = Officer
    template_name = "base/officers.html"

    def get_queryset(self):
        return Officer.objects.filter(term=self.display_term).order_by(
            'position__rank', '-is_chair').select_related(
            'user__userprofile', 'user__studentorguserprofile', 'position')
