from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView
from django.views.generic import ListView

from quark.courses.models import Course
from quark.courses.models import CourseInstance
from quark.courses.models import Department
from quark.course_surveys.models import Survey
from quark.exam_files.models import Exam


class DepartmentListView(ListView):
    context_object_name = 'department_list'
    template_name = 'courses/department_list.html'

    def get_queryset(self):
        courses_with_surveys = Course.objects.filter(survey__published=True)
        courses_with_exams = Course.objects.filter(
            courseinstance__in=CourseInstance.objects.filter(
                exam__approved=True))
        return Department.objects.filter(
            Q(course__in=courses_with_surveys) |
            Q(course__in=courses_with_exams)).order_by('long_name')


class CourseListView(ListView):
    context_object_name = 'course_list'
    template_name = 'courses/course_list.html'

    def get_queryset(self):
        courses_query = Course.objects.filter(
            Q(survey__published=True) |
            Q(courseinstance__in=CourseInstance.objects.filter(
                exam__approved=True)),
            department__slug=self.kwargs['dept_slug'])
        if not courses_query.exists():
            raise Http404
        return courses_query


class CourseDetailView(DetailView):
    context_object_name = 'course'
    template_name = 'courses/course_details.html'

    def get_object(self, queryset=None):
        return get_object_or_404(Course,
                                 department__slug=self.kwargs['dept_slug'],
                                 number=self.kwargs['course_num'])

    def get_context_data(self, **kwargs):
        context = super(CourseDetailView, self).get_context_data(**kwargs)
        context['course_instances'] = CourseInstance.objects.filter(
            course=self.get_object())
        context['exams'] = Exam.objects.filter(
            course_instance__course=self.get_object())
        context['surveys'] = Survey.objects.filter(course=self.get_object())
        return context
