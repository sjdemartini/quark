from django import forms

from quark.auth.models import User
from quark.auth.fields import UserCommonNameMultipleChoiceField
from quark.quote_board.models import Quote


class QuoteForm(forms.ModelForm):
    speakers = UserCommonNameMultipleChoiceField(queryset=User.objects.all())

    class Meta:
        model = Quote
        exclude = ('submitter',)
