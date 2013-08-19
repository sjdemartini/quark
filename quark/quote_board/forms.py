from django import forms
from django.contrib.auth import get_user_model

from quark.quote_board.models import Quote
from quark.user_profiles.fields import UserCommonNameMultipleChoiceField


class QuoteForm(forms.ModelForm):
    speakers = UserCommonNameMultipleChoiceField(
        queryset=get_user_model().objects.all())

    class Meta(object):
        model = Quote
        exclude = ('submitter',)
