from django import forms

from quark.base.fields import VisualDateWidget
from quark.base.forms import ChosenTermMixin
from quark.minutes.models import Minutes
from quark.shortcuts import get_file_mimetype


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
    notes = forms.FileField(
        label='Upload Minutes (Text File)',
        widget=forms.FileInput(attrs={'accept': 'text/plain'}))

    def clean_notes(self):
        """Check that the uploaded file is a text file."""
        notes = self.cleaned_data['notes']
        if get_file_mimetype(notes) != 'text/plain':
            raise forms.ValidationError('Uploaded file must be a text file.')
        return notes
