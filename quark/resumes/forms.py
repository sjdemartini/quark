from django import forms
from django.forms import formsets

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


class ResumeListForm(forms.ModelForm):
    # TODO(ericdwang): NullBooleanFields show an extra blank field when using
    # custom choices. This field can be removed (so Resume.VERIFIED_CHOICES
    # would be used instead) when Django fixes the bug.
    verified = forms.NullBooleanField()

    class Meta(object):
        model = Resume
        fields = ('verified',)


class BaseResumeListForm(formsets.BaseFormSet):
    def total_form_count(self):
        return Resume.objects.all().count()


class ResumeVerifyForm(forms.ModelForm):
    # TODO(ericdwang): NullBooleanFields show an extra blank field when using
    # custom choices. This field can be removed (so Resume.VERIFIED_CHOICES
    # would be used instead) when Django fixes the bug.
    verified = forms.NullBooleanField()

    class Meta(object):
        model = Resume
        fields = ('verified',)


class BaseResumeVerifyForm(formsets.BaseFormSet):
    def total_form_count(self):
        return Resume.objects.filter(verified__isnull=True).count()


class ResumeCritiqueForm(forms.ModelForm):
    class Meta(object):
        model = Resume
        fields = ('critique',)

    def clean(self):
        cleaned_data = super(ResumeCritiqueForm, self).clean()
        # save the inverse of the value indicated under the
        # "critique completed" column to resume.critique.
        cleaned_data['critique'] = not cleaned_data['critique']
        return cleaned_data


class BaseResumeCritiqueForm(formsets.BaseFormSet):
    def total_form_count(self):
        return Resume.objects.filter(critique=True).count()

# pylint: disable=C0103
ResumeListFormSet = formsets.formset_factory(
    ResumeListForm, formset=BaseResumeListForm)

# pylint: disable=C0103
ResumeVerifyFormSet = formsets.formset_factory(
    ResumeVerifyForm, formset=BaseResumeVerifyForm)

# pylint: disable=C0103
ResumeCritiqueFormSet = formsets.formset_factory(
    ResumeCritiqueForm, formset=BaseResumeCritiqueForm)
