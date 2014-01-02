from django import forms

from quark.resumes.models import Resume
from quark.shortcuts import get_file_mimetype


class ResumeForm(forms.ModelForm):
    gpa = forms.DecimalField(
        label='GPA', min_value=0, max_value=4,
        widget=forms.TextInput(attrs={'size': 5, 'maxlength': 5}),
        help_text='GPA must have three decimal places (ex. 3.750)')
    resume_file = forms.FileField(
        label='File (PDF only please)',
        widget=forms.FileInput(attrs={'accept': 'application/pdf'}))

    class Meta(object):
        model = Resume
        fields = ('gpa', 'full_text', 'resume_file', 'critique', 'release')

    def clean_resume_file(self):
        """Check if uploaded file is of an acceptable format."""
        resume_file = self.cleaned_data.get('resume_file')
        if get_file_mimetype(resume_file) != 'application/pdf':
            raise forms.ValidationError('Uploaded file must be a PDF file.')
        return resume_file
