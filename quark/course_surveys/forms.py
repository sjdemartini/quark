from chosen import widgets as ChosenWidgets
from django import forms

from quark.base.forms import ChosenTermMixin
from quark.courses.models import Course
from quark.courses.models import Department
from quark.courses.models import Instructor
from quark.course_surveys.models import Survey


def courses_as_optgroups():
    """
    Returns nested lists where the courses have a department title in
    the selection widget. Used in the 'choices' field for 'course'.
    For example:
    Computer Science
        CS 10
        CS 61A
        CS 61B
        ...
    """
    course_choices = []
    for dept in Department.objects.order_by('long_name'):
        courses_in_dept = []
        for course in Course.objects.filter(department=dept):
            courses_in_dept.append([course, course.abbreviation()])
        curr_dept = [dept.long_name, courses_in_dept]
        course_choices.append(curr_dept)
    return course_choices


class SurveyForm(ChosenTermMixin, forms.ModelForm):
    class Meta(object):
        model = Survey
        exclude = ('submitter', 'published', 'created')
        widgets = {
            'course': ChosenWidgets.ChosenGroupSelect(),
            'instructor': ChosenWidgets.ChosenSelect()
        }

    def __init__(self, *args, **kwargs):
        super(SurveyForm, self).__init__(*args, **kwargs)
        # Create fields in __init__ to avoid database errors in Django's test
        # runner caused by trying to use functions that aren't "lazy" that
        # access the database
        self.fields['course'].label = 'Course Number'
        self.fields['course'].choices = courses_as_optgroups()
        self.fields['instructor'].label = 'Instructor'
        self.fields['instructor'].queryset = Instructor.objects.order_by(
            'name')
