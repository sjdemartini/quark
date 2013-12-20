from django import forms

from quark.quote_board.models import Quote
from quark.user_profiles.fields import UserCommonNameMultipleChoiceField


class QuoteForm(forms.ModelForm):
    speakers = UserCommonNameMultipleChoiceField()

    class Meta(object):
        model = Quote
        exclude = ('submitter',)
