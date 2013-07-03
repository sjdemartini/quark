from django import forms
from django.contrib.auth import get_user_model

from quark.accounts.fields import UserCommonNameMultipleChoiceField
from quark.quote_board.models import Quote


class QuoteForm(forms.ModelForm):
    speakers = UserCommonNameMultipleChoiceField(
        queryset=get_user_model().objects.all())

    class Meta:
        model = Quote
        exclude = ('submitter',)
