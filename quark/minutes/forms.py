from django import forms

from quark.minutes.models import Minutes


class MinutesForm(forms.ModelForm):
    class Meta:
        model = Minutes
        exclude = ('author',)


class InputForm(MinutesForm):
    notes = forms.CharField(widget=forms.Textarea, label='Meeting Minutes')


class UploadForm(MinutesForm):
    notes = forms.FileField(label='Upload Minutes')
