from django import forms

from quark.base.models import RandomToken


# pylint: disable=R0924
class RandomTokenForm(forms.ModelForm):
    """
    Basic form that asks for an email.
    Auto-generates a random token.
    """
    class Meta:
        model = RandomToken
        fields = ('email',)
