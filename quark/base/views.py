from django.shortcuts import render

from quark.base.models import Term


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
        context['is_current'] = self.is_current

        # Add queryset of all Terms up to and including the current term,
        # ordered from current to oldest
        context['terms'] = Term.objects.get_terms(reverse=True)
        return context
