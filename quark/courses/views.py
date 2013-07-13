from django.db.models import Avg
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView
from django.views.generic import ListView

from quark.courses.models import Course
from quark.courses.models import CourseInstance
from quark.courses.models import Department
from quark.courses.models import Instructor
from quark.course_surveys.models import Survey
from quark.exams.models import Exam


class DepartmentListView(ListView):
    context_object_name = 'department_list'
    template_name = 'courses/department_list.html'

    def get_queryset(self):
        courses_with_surveys = Course.objects.filter(survey__published=True)
        course_ids = Exam.objects.get_approved().values_list(
            'course_instance__course_id', flat=True)
        courses_with_exams = Course.objects.filter(id__in=course_ids)
        return Department.objects.filter(
            Q(course__in=courses_with_surveys) |
            Q(course__in=courses_with_exams)).order_by('long_name').distinct()


class CourseListView(ListView):
    context_object_name = 'course_list'
    template_name = 'courses/course_list.html'
    dept = None

    def dispatch(self, *args, **kwargs):
        self.dept = get_object_or_404(Department,
                                      slug=self.kwargs['dept_slug'].lower())
        return super(CourseListView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        course_instance_ids = Exam.objects.get_approved().values_list(
            'course_instance_id', flat=True)
        course_instances_with_exams = CourseInstance.objects.filter(
            id__in=course_instance_ids)
        courses_query = Course.objects.filter(
            Q(survey__published=True) |
            Q(courseinstance__in=course_instances_with_exams),
            department=self.dept).distinct()
        if not courses_query.exists():
            raise Http404
        return courses_query

    def get_context_data(self, **kwargs):
        context = super(CourseListView, self).get_context_data(**kwargs)
        context['department'] = self.dept
        return context


class CourseDetailView(DetailView):
    context_object_name = 'course'
    template_name = 'courses/course_details.html'
    course = None

    def get_object(self, queryset=None):
        self.course = get_object_or_404(
            Course,
            department__slug=self.kwargs['dept_slug'].lower(),
            number=self.kwargs['course_num'])
        return self.course

    def get_context_data(self, **kwargs):
        context = super(CourseDetailView, self).get_context_data(**kwargs)
        context['course_instances'] = CourseInstance.objects.filter(
            course=self.course)
        context['exams'] = Exam.objects.get_approved().filter(
            course_instance__course=self.course)
        context['surveys'] = Survey.objects.filter(course=self.course)
        context['instructors'] = Instructor.objects.filter(
            survey__in=context['course_instances'])
        # Average of course_rating values across all surveys for this course
        context['total_course_ratings_avg'] = context['surveys'].aggregate(
            Avg('course_rating'))['course_rating__avg']
        # For each instructor, average the prof_rating and course_rating
        # across that instructor's surveys, and put them in the dictionaries
        # prof_ratings_avg and course_ratings_avg with key = instructor,
        # value = avg_rating
        prof_ratings_avg = dict()
        course_ratings_avg = dict()
        for inst in context['instructors']:
            ratings = context['surveys'].filter(instructor=inst).aggregate(
                Avg('prof_rating'), Avg('course_rating'))
            prof_ratings_avg[inst.full_name()] = (
                ratings['prof_rating__avg'])
            course_ratings_avg[inst.full_name()] = (
                ratings['course_rating__avg'])
        context['prof_ratings_avg'] = prof_ratings_avg
        context['course_ratings_avg'] = course_ratings_avg
        return context


class InstructorDetailView(DetailView):
    context_object_name = 'instructor'
    template_name = 'courses/instructor_details.html'
    instructor = None

    def get_object(self, queryset=None):
        self.instructor = get_object_or_404(Instructor,
                                            pk=self.kwargs['inst_pk'])
        return self.instructor

    def get_context_data(self, **kwargs):
        context = super(InstructorDetailView, self).get_context_data(**kwargs)
        context['course_instances'] = CourseInstance.objects.filter(
            instructors=self.instructor)
        context['exams'] = Exam.objects.get_approved().filter(
            course_instance__in=context['course_instances'])
        context['surveys'] = Survey.objects.filter(instructor=self.instructor)
        context['courses'] = Course.objects.filter(
            courseinstance__in=context['course_instances'])
        context['total_prof_ratings_avg'] = context['surveys'].aggregate(
            Avg('prof_rating'))['prof_rating__avg']
        # For each course that this instructor has taught, average the
        # prof_rating course_rating across the instructor's surveys for each
        # course, and put them in the dictionaries prof_ratings_avg and
        # course_ratings_avg  with key = course.abbreviation(),
        # value = avg_rating
        prof_ratings_avg = dict()
        course_ratings_avg = dict()
        for course in context['courses']:
            ratings = context['surveys'].filter(course=course).aggregate(
                Avg('prof_rating'), Avg('course_rating'))
            prof_ratings_avg[course.abbreviation()] = (
                ratings['prof_rating__avg'])
            course_ratings_avg[course.abbreviation()] = (
                ratings['course_rating__avg'])
        context['prof_ratings_avg'] = prof_ratings_avg
        context['course_ratings_avg'] = course_ratings_avg
        return context
