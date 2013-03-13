import os

from chosen import forms as chosen_forms
from django import forms
from django.utils.safestring import mark_safe

from quark.base.models import Term
from quark.courses.models import CourseInstance
from quark.courses.models import Instructor
from quark.course_surveys.forms import courses_as_optgroups
from quark.exam_files.models import Exam
from quark.exam_files.models import ExamFlag
from quark.exam_files.models import InstructorPermission


class ExamForm(forms.ModelForm):
    """Used as a base for UploadForm and EditForm."""
    exam = forms.ChoiceField(label='Exam', choices=Exam.EXAM_CHOICES)
    exam_type = forms.ChoiceField(
        label='Exam or solution file?', choices=Exam.EXAM_TYPE_CHOICES)
    instructors = chosen_forms.ChosenModelMultipleChoiceField(
        label='Instructors', queryset=Instructor.objects.all())

    class Meta:
        model = Exam
        fields = ('exam', 'exam_type')
        chosen_forms.widgets = {
            'course': chosen_forms.ChosenGroupSelect(),
            'term': chosen_forms.ChosenSelect(),
        }

    def __init__(self, *args, **kwargs):
        super(ExamForm, self).__init__(*args, **kwargs)
        # Create fields in __init__ to avoid database errors in Django's test
        # runner caused by trying to use functions that aren't "lazy" that
        # access the database
        self.fields['course'].label = 'Course Number'
        self.fields['course'].choices = courses_as_optgroups()
        self.fields['term'].label = 'Term'
        self.fields['term'].queryset = Term.objects.get_terms(
            include_summer=True)

    def check_duplicates(self, cleaned_data, message):
        """Check for duplicate exams."""
        duplicates = Exam.objects.filter(
            course_instance__course=cleaned_data.get('course'),
            course_instance__term=cleaned_data.get('term'),
            exam=cleaned_data.get('exam'),
            exam_type=cleaned_data.get('exam_type'))
        if duplicates.count() > 0:
            raise forms.ValidationError(
                'This exam already exists in the database. ' + message)
        return cleaned_data

    def save(self, *args, **kwargs):
        """Add a course instance to the exam."""
        exam = super(ExamForm, self).save(*args, **kwargs)
        course_instance = CourseInstance.objects.get(
            course=self.cleaned_data.get('course'),
            term=self.cleaned_data.get('term'))
        exam.course_instance = course_instance
        exam.save()
        return exam


class UploadForm(ExamForm):
    ACCEPTED_FORMATS = ['.pdf', '.doc', '.docx', '.rtf']

    exam_file = forms.FileField(label='File (pdf or doc only please)')
    agreed = forms.BooleanField(required=True, label=mark_safe(
        'I agree, per campus policy on Course Note-Taking and Materials '
        '(available <a href="http://campuspol.chance.berkeley.edu/policies/'
        'coursenotes.pdf">here</a>), that I am allowed to upload '
        'this document.'))

    class Meta(ExamForm.Meta):
        fields = ('exam', 'exam_type', 'exam_file')

    def clean(self):
        """Check if uploaded exam already exists, whether the file is of
        an acceptable format, and whether the professor is blacklisted."""
        cleaned_data = super(UploadForm, self).clean()
        # check for duplicates
        cleaned_data = self.check_duplicates(
            cleaned_data, 'Please upload a new exam.')

        # check if uploaded file is doc or pdf
        file_ext = os.path.splitext(cleaned_data.get('exam_file').name)[1]
        if file_ext not in ExamForm.ACCEPTED_FORMATS:
            raise forms.ValidationError(
                'Uploaded file must be an MSWord doc or PDF file.')
        return cleaned_data

    def save(self, *args, **kwargs):
        """Check if professors are blacklisted."""
        exam = super(UploadForm, self).save(*args, **kwargs)
        for instructor in self.cleaned_data.get('instructors'):
            permission = InstructorPermission.objects.get(
                instructor=instructor).permission_allowed
            if not permission:
                exam.blacklisted = True
        exam.save()
        return exam


class EditForm(ExamForm):
    approved = forms.BooleanField(label='Approved')

    class Meta(ExamForm.Meta):
        fields = ('exam', 'exam_type', 'approved')

    def clean(self):
        """Check if an exam already exists with the new changes."""
        cleaned_data = super(EditForm, self).clean()
        # check for duplicates
        return self.check_duplicates(
            cleaned_data, 'Please double check and delete as necessary.')


class FlagForm(forms.ModelForm):
    reason = forms.CharField(widget=forms.Textarea, label='Reason')

    class Meta:
        model = ExamFlag
        fields = ('reason',)

    def clean_reason(self):
        if len(self.cleaned_data.get('reason')) < 10:
            raise forms.ValidationError('Please be more descriptive.')
        return super(FlagForm, self).clean()


class ResolveFlagForm(forms.ModelForm):
    resolution = forms.CharField(widget=forms.Textarea, label='Resolution')

    class Meta:
        model = ExamFlag
        fields = ('resolution',)

    def clean_reason(self):
        if len(self.cleaned_data.get('resolution')) < 10:
            raise forms.ValidationError('Please be more descriptive.')
        return super(ResolveFlagForm, self).clean()
