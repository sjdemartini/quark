from chosen import forms as chosen_forms
from django import forms
from django.db.models import Count
from django.utils.safestring import mark_safe

from quark.base.forms import ChosenTermMixin
from quark.courses.models import Course
from quark.courses.models import CourseInstance
from quark.courses.models import Department
from quark.courses.models import Instructor
from quark.exams.models import Exam
from quark.exams.models import ExamFlag
from quark.exams.models import InstructorPermission
from quark.shortcuts import get_file_mimetype
from quark.shortcuts import get_object_or_none


class ExamForm(ChosenTermMixin, forms.ModelForm):
    """Used as a base for UploadForm and EditForm."""
    department = chosen_forms.ChosenModelChoiceField(
        queryset=Department.objects.all())
    course_number = forms.CharField()
    instructors = chosen_forms.ChosenModelMultipleChoiceField(
        queryset=Instructor.objects.all())

    course_instance = None  # set by set_course_instance
    instructors = None  # set by set_course_instance

    class Meta(object):
        model = Exam
        fields = ('exam_number', 'exam_type')

    def __init__(self, *args, **kwargs):
        super(ExamForm, self).__init__(*args, **kwargs)
        self.fields['exam_type'].label = 'Exam or solution file?'
        self.fields.keyOrder = [
            'department', 'course_number', 'instructors', 'term', 'exam_number',
            'exam_type']

    def set_course_instance(self, cleaned_data):
        """Check if a course is valid and whether a course instance exists
        with the exact instructors given, and create a course instance if one
        doesn't exist.
        """
        department = self.cleaned_data.get('department')
        course_number = self.cleaned_data.get('course_number')
        term = self.cleaned_data.get('term')

        course = get_object_or_none(
            Course, department=department, number=course_number)
        if not course:
            error_msg = '{department} {number} does not exist.'.format(
                department=department, number=course_number)
            self._errors['department'] = self.error_class([error_msg])
            self._errors['course_number'] = self.error_class([error_msg])
            raise forms.ValidationError('Invalid course')

        # check instructors to prevent trying to iterate over nothing
        self.instructors = self.cleaned_data.get('instructors')
        if not self.instructors:
            raise forms.ValidationError('Please fill out all fields.')

        course_instance = CourseInstance.objects.annotate(
            count=Count('instructors')).filter(
            count=len(self.instructors),
            term=term,
            course=course)
        for instructor in self.instructors:
            course_instance = course_instance.filter(instructors=instructor)
        if course_instance.exists():
            course_instance = course_instance.get()
        else:
            course_instance = CourseInstance.objects.create(
                term=term, course=course)
            course_instance.instructors.add(*self.instructors)
            course_instance.save()
        self.course_instance = course_instance

    def save(self, *args, **kwargs):
        """Add a course instance to the exam."""
        self.instance.course_instance = self.course_instance
        return super(ExamForm, self).save(*args, **kwargs)


class UploadForm(ExamForm):
    # Remove the "Unknown" choice when uploading
    exam_number = forms.ChoiceField(choices=Exam.EXAM_NUMBER_CHOICES[1:])
    exam_file = forms.FileField(
        label='File (PDF only please)',
        widget=forms.FileInput(attrs={'accept': 'application/pdf'}))
    agreed = forms.BooleanField(required=True, label=mark_safe(
        'I agree, per campus policy on Course Note-Taking and Materials '
        '(available <a href="http://campuspol.chance.berkeley.edu/policies/'
        'coursenotes.pdf">here</a>), that I am allowed to upload '
        'this document.'))

    class Meta(ExamForm.Meta):
        fields = ExamForm.Meta.fields + ('exam_file',)

    def __init__(self, *args, **kwargs):
        super(UploadForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder += ['exam_file', 'agreed']

    def clean_exam_file(self):
        """Check if uploaded exam file is of an acceptable format."""
        exam_file = self.cleaned_data.get('exam_file')
        if get_file_mimetype(exam_file) != 'application/pdf':
            raise forms.ValidationError('Uploaded file must be a PDF file.')
        return exam_file

    def clean(self):
        """Check if uploaded exam already exists."""
        cleaned_data = super(UploadForm, self).clean()
        self.set_course_instance(cleaned_data)
        duplicates = Exam.objects.filter(
            course_instance=self.course_instance,
            exam_number=cleaned_data.get('exam_number'),
            exam_type=cleaned_data.get('exam_type'))
        if duplicates.exists():
            raise forms.ValidationError(
                'This exam already exists in the database.')
        return cleaned_data

    def save(self, *args, **kwargs):
        """Check if professors are blacklisted."""
        for instructor in self.instructors:
            permission, _ = InstructorPermission.objects.get_or_create(
                instructor=instructor)
            if permission.permission_allowed is False:
                self.instance.blacklisted = True
        return super(UploadForm, self).save(*args, **kwargs)


class EditForm(ExamForm):
    class Meta(ExamForm.Meta):
        fields = ExamForm.Meta.fields + ('verified',)

    def __init__(self, *args, **kwargs):
        super(EditForm, self).__init__(*args, **kwargs)
        self.fields['department'].initial = (
            self.instance.course_instance.course.department)
        self.fields['course_number'].initial = (
            self.instance.course_instance.course.number)
        self.fields['instructors'].initial = (
            self.instance.course_instance.instructors.all())
        self.fields['term'].initial = self.instance.course_instance.term
        self.fields.keyOrder += ['verified']

    def clean(self):
        """Check if an exam already exists with the new changes, excluding the
        current exam being edited.
        """
        cleaned_data = super(EditForm, self).clean()
        self.set_course_instance(cleaned_data)
        duplicates = Exam.objects.filter(
            course_instance=self.course_instance,
            exam_number=cleaned_data.get('exam_number'),
            exam_type=cleaned_data.get('exam_type')).exclude(
            pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError(
                'This exam already exists in the database. '
                'Please double check and delete as necessary.')
        return cleaned_data


class FlagForm(forms.ModelForm):
    class Meta(object):
        model = ExamFlag
        fields = ('reason',)


class FlagResolveForm(forms.ModelForm):
    class Meta(object):
        model = ExamFlag
        fields = ('resolution',)


class EditPermissionForm(forms.ModelForm):
    permission_allowed = forms.NullBooleanField()

    class Meta(object):
        model = InstructorPermission
        fields = ('permission_allowed', 'correspondence')


class BaseEditPermissionFormset(forms.formsets.BaseFormSet):
    def total_form_count(self):
        """Sets the number of forms equal to the number of instructor
        permissions.
        """
        return InstructorPermission.objects.all().count()


# pylint: disable=C0103
EditPermissionFormSet = forms.formsets.formset_factory(
    EditPermissionForm, formset=BaseEditPermissionFormset)
