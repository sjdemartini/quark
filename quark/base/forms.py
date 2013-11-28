from chosen import forms as chosen_forms

from quark.base.models import Term


class ChosenTermMixin(object):
    """Form mixin to use Chosen for the "term" form field.

    This mixin is useful because the queryset is commonly used for term
    selection in a form, where all terms up to and including the current term
    are listed in reverse order.
    """
    def __init__(self, *args, **kwargs):
        super(ChosenTermMixin, self).__init__(*args, **kwargs)

        # For fields which reference a QuerySet that must be evaluated (i.e,
        # hits the database and isn't "lazy"), create fields in the __init__ to
        # avoid database errors in Django's test runner
        self.fields['term'] = chosen_forms.ChosenModelChoiceField(
            queryset=Term.objects.get_terms(
                include_future=False, include_summer=True, reverse=True),
            initial=Term.objects.get_current_term())
