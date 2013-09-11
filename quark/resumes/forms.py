import magic

from django import forms

from quark.resumes.models import Resume


class ResumeForm(forms.ModelForm):
    gpa = forms.DecimalField(
        label='GPA', min_value=0, max_value=4,
        widget=forms.TextInput(attrs={'size': 5, 'maxlength': 5}),
        help_text='GPA must have three decimal places (ex. 3.750)')

    class Meta(object):
        model = Resume
        fields = ('gpa', 'full_text', 'resume_file', 'critique', 'release')

    def clean(self):
        """Check if uploaded file is of an acceptable format."""
        cleaned_data = super(ResumeForm, self).clean()
        # check if a file was actually uploaded
        resume_file = cleaned_data.get('resume_file')
        if not resume_file:
            raise forms.ValidationError('Please attach a file.')

        # Use python-magic to verify the file type so someone cannot upload
        # an unallowed file type by simply changing the file extension.
        # If the uploaded file is greater than 2.5MB (if multiple_chunks()
        # returns True), then it will be stored temporarily on disk;
        # otherwise, it will be stored in memory.
        if resume_file.multiple_chunks():
            output = magic.from_file(
                resume_file.temporary_file_path(), mime=True)
        else:
            output = magic.from_buffer(resume_file.read(), mime=True)
        if output != 'application/pdf':
            raise forms.ValidationError('Uploaded file must be a PDF file.')
        return cleaned_data
