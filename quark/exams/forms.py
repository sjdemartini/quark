import magic

from chosen import forms as chosen_forms
from django import forms
from django.utils.safestring import mark_safe

from quark.base.models import Term
from quark.courses.models import CourseInstance
from quark.courses.models import Department
from quark.courses.models import Instructor
from quark.exams.models import Exam
from quark.exams.models import ExamFlag
from quark.exams.models import InstructorPermission


class ExamForm(forms.ModelForm):
    """Used as a base for UploadForm and EditForm."""
    department = chosen_forms.ChosenModelChoiceField(
        label='Department', queryset=Department.objects.all())
    course_number = forms.CharField()
    instructors = chosen_forms.ChosenModelMultipleChoiceField(
        label='Instructors', queryset=Instructor.objects.all())
    exam_number = chosen_forms.ChosenChoiceField(
        label='Exam Number', choices=Exam.EXAM_NUMBER_CHOICES)
    exam_type = chosen_forms.ChosenChoiceField(
        label='Exam or solution file?', choices=Exam.EXAM_TYPE_CHOICES)

    course_instance = None  # set by check_course_instance

    def __init__(self, *args, **kwargs):
        super(ExamForm, self).__init__(*args, **kwargs)
        self.fields['term'] = chosen_forms.ChosenModelChoiceField(
            label='Term', queryset=Term.objects.get_terms(include_summer=True))

    def check_course_instance(self, cleaned_data):
        """Check if the course instance exists."""
        course_instance = CourseInstance.objects.filter(
            course__department=self.cleaned_data.get('department'),
            course__number=self.cleaned_data.get('course_number'),
            term=self.cleaned_data.get('term'))
        # check instructors to prevent trying to iterate over nothing
        if self.cleaned_data.get('instructors') is None:
            raise forms.ValidationError('Please fill out all fields.')
        for instructor in self.cleaned_data.get('instructors'):
            course_instance = course_instance.filter(instructors=instructor)
        if len(course_instance) == 0:
            instructors = ', '.join(
                [i.last_name for i in self.cleaned_data.get('instructors')])
            raise forms.ValidationError(
                '{department} {number} ({term}), taught by {instructors}'
                ' never existed.'.format(
                    term=self.cleaned_data.get('term').verbose_name(),
                    department=self.cleaned_data.get('department'),
                    number=self.cleaned_data.get('course_number'),
                    instructors=instructors))
        self.course_instance = course_instance[0]

    def save(self, *args, **kwargs):
        """Add a course instance to the exam."""
        self.instance.course_instance = self.course_instance
        return super(ExamForm, self).save(*args, **kwargs)


class UploadForm(ExamForm):
    exam_file = forms.FileField(
        label='File (PDF only please)')
    agreed = forms.BooleanField(required=True, label=mark_safe(
        'I agree, per campus policy on Course Note-Taking and Materials '
        '(available <a href="http://campuspol.chance.berkeley.edu/policies/'
        'coursenotes.pdf">here</a>), that I am allowed to upload '
        'this document.'))

    class Meta:
        model = Exam
        fields = ('exam_number', 'exam_type', 'exam_file')

    def __init__(self, *args, **kwargs):
        super(UploadForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = [
            'department', 'course_number', 'instructors', 'term', 'exam_number',
            'exam_type', 'exam_file', 'agreed']

    def clean(self):
        """Check if uploaded exam already exists and whether the file is of
        an acceptable format."""
        cleaned_data = super(UploadForm, self).clean()
        self.check_course_instance(cleaned_data)
        duplicates = Exam.objects.filter(
            course_instance=self.course_instance,
            exam_number=cleaned_data.get('exam_number'),
            exam_type=cleaned_data.get('exam_type'))
        if duplicates.count() > 0:
            raise forms.ValidationError(
                'This exam already exists in the database. '
                'Please upload a new exam.')

        # check if a file was actually uploaded
        exam_file = cleaned_data.get('exam_file')
        if not exam_file:
            raise forms.ValidationError('Please attach a file.')

        # Use python-magic to verify the file type so someone cannot upload
        # an unallowed file type by simply changing the file extension.
        # If the uploaded file is greater than 2.5MB (if multiple_chunks()
        # returns True), then it will be stored temporarily on disk;
        # otherwise, it will be stored in memory.
        if exam_file.multiple_chunks():
            output = magic.from_file(exam_file.temporary_file_path(), mime=True)
        else:
            output = magic.from_buffer(exam_file.read(), mime=True)
        if output != 'application/pdf':
            raise forms.ValidationError('Uploaded file must be a PDF file.')
        return cleaned_data

    def save(self, *args, **kwargs):
        """Check if professors are blacklisted."""
        for instructor in self.cleaned_data.get('instructors'):
            permission = InstructorPermission.objects.get_or_create(
                instructor=instructor)[0].permission_allowed
            if permission is False:
                self.instance.blacklisted = True
        return super(UploadForm, self).save(*args, **kwargs)


class EditForm(ExamForm):
    verified = forms.BooleanField(label='Verified', required=False)

    class Meta:
        model = Exam
        fields = ('exam_number', 'exam_type', 'verified')

    def __init__(self, *args, **kwargs):
        super(EditForm, self).__init__(*args, **kwargs)
        self.fields['department'].initial = (
            self.instance.course_instance.course.department)
        self.fields['course_number'].initial = (
            self.instance.course_instance.course.number)
        self.fields['instructors'].initial = (
            self.instance.course_instance.instructors.all())
        self.fields['term'].initial = self.instance.course_instance.term
        self.fields.keyOrder = [
            'department', 'course_number', 'instructors', 'term', 'exam_number',
            'exam_type', 'verified']

    def clean(self):
        """Check if an exam already exists with the new changes."""
        cleaned_data = super(EditForm, self).clean()
        self.check_course_instance(cleaned_data)
        duplicates = Exam.objects.filter(
            course_instance=self.course_instance,
            exam_number=cleaned_data.get('exam_number'),
            exam_type=cleaned_data.get('exam_type'),
            verified=cleaned_data.get('verified'))
        if duplicates.count() > 0:
            raise forms.ValidationError(
                'This exam already exists in the database. '
                'Please double check and delete as necessary.')
        return cleaned_data


class FlagForm(forms.ModelForm):
    reason = forms.CharField(widget=forms.Textarea, label='Reason')

    class Meta:
        model = ExamFlag
        fields = ('reason',)


class FlagResolveForm(forms.ModelForm):
    resolution = forms.CharField(widget=forms.Textarea, label='Resolution')

    class Meta:
        model = ExamFlag
        fields = ('resolution',)


class EditPermissionForm(forms.ModelForm):
    permission_allowed = forms.NullBooleanField(label='Permission allowed')
    correspondence = forms.CharField(
        widget=forms.Textarea, label='Correspondence', required=False)

    class Meta:
        model = InstructorPermission
        fields = ('permission_allowed', 'correspondence')
