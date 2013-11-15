from django import forms

from quark.base.fields import VisualDateWidget
from quark.base.forms import ChosenTermMixin
from quark.minutes.models import Minutes


class MinutesForm(ChosenTermMixin, forms.ModelForm):
    class Meta(object):
        model = Minutes
        exclude = ('author',)
        widgets = {
            'date': VisualDateWidget(),
        }


class InputForm(MinutesForm):
    notes = forms.CharField(widget=forms.Textarea, label='Meeting Minutes')


class UploadForm(MinutesForm):
    notes = forms.FileField(label='Upload Minutes (Text File)')
