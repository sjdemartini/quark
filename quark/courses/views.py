from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.core.urlresolvers import reverse
from django.db.models import Avg
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView

from quark.courses.forms import InstructorEditForm
from quark.courses.forms import InstructorForm
from quark.courses.models import Course
from quark.courses.models import CourseInstance
from quark.courses.models import Department
from quark.courses.models import Instructor
from quark.course_surveys.models import Survey
from quark.exams.models import Exam


class CourseDepartmentListView(ListView):
    context_object_name = 'departments'
    template_name = 'courses/course_department_list.html'

    def get_queryset(self):
        courses_with_surveys = Course.objects.filter(survey__published=True)
        course_pks = Exam.objects.get_approved().values_list(
            'course_instance__course__pk', flat=True)
        courses_with_exams = Course.objects.filter(pk__in=course_pks)
        return Department.objects.filter(
            Q(course__in=courses_with_surveys) |
            Q(course__in=courses_with_exams)).distinct()


class CourseListView(ListView):
    context_object_name = 'courses'
    template_name = 'courses/course_list.html'
    dept = None

    def dispatch(self, *args, **kwargs):
        self.dept = get_object_or_404(Department,
                                      slug=self.kwargs['dept_slug'].lower())
        return super(CourseListView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        courses_with_exams_pks = Exam.objects.get_approved().values_list(
            'course_instance__course__pk', flat=True)
        courses_query = Course.objects.select_related('department').filter(
            Q(survey__published=True) |
            Q(pk__in=courses_with_exams_pks),
            department=self.dept).distinct()
        if not courses_query.exists():
            raise Http404
        return sorted(courses_query)

    def get_context_data(self, **kwargs):
        context = super(CourseListView, self).get_context_data(**kwargs)
        context['department'] = self.dept
        return context


class CourseDetailView(DetailView):
    context_object_name = 'course'
    template_name = 'courses/course_detail.html'
    course = None

    def get_object(self, queryset=None):
        self.course = get_object_or_404(
            Course,
            department__slug=self.kwargs['dept_slug'].lower(),
            number=self.kwargs['course_num'])
        return self.course

    def get_context_data(self, **kwargs):
        context = super(CourseDetailView, self).get_context_data(**kwargs)

        # Get all exams for the course
        context['exams'] = Exam.objects.get_approved().filter(
            course_instance__course=self.course).select_related(
            'course_instance__term',
            'course_instance__course__department').prefetch_related(
            'course_instance__instructors')

        # Get all surveys for the course
        surveys = Survey.objects.filter(course=self.course)
        context['surveys'] = surveys

        # TODO(ericdwang): re-add course ratings
#        # Get average course rating and instructor ratings for the course
#        # course_instances = CourseInstance.objects.filter(course=self.course)
#        instructors = Instructor.objects.filter(
#            courseinstance__in=course_instances).distinct()
#        context['instructors'] = instructors
#        Average of course_rating values across all surveys for this course
#        context['total_course_ratings_avg'] = surveys.aggregate(
#            Avg('course_rating'))['course_rating__avg']
#        # For each instructor, average the prof_rating and course_rating
#        # across that instructor's surveys, and put them in the dictionaries
#        # prof_ratings_avg and course_ratings_avg with key = instructor,
#        value = avg_rating
#        prof_ratings_avg = dict()
#        course_ratings_avg = dict()
#        for inst in instructors:
#            ratings = surveys.filter(instructor=inst).aggregate(
#                Avg('prof_rating'), Avg('course_rating'))
#            prof_ratings_avg[inst.pk] = (
#                ratings['prof_rating__avg'])
#            course_ratings_avg[inst.pk] = (
#                ratings['course_rating__avg'])
#        context['prof_ratings_avg'] = prof_ratings_avg
#        context['course_ratings_avg'] = course_ratings_avg
        return context


class InstructorCreateView(CreateView):
    form_class = InstructorForm
    template_name = 'courses/add_instructor.html'

    @method_decorator(login_required)
    @method_decorator(
        permission_required('courses.add_instructor', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(InstructorCreateView, self).dispatch(
            *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'Instructor added!')
        return super(InstructorCreateView, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct your input fields.')
        return super(InstructorCreateView, self).form_invalid(form)


class InstructorDepartmentListView(ListView):
    context_object_name = 'departments'
    template_name = 'courses/instructor_department_list.html'

    def get_queryset(self):
        instructors = Instructor.objects.all()
        return Department.objects.filter(instructor__in=instructors).distinct()


class InstructorListView(ListView):
    context_object_name = 'instructors'
    template_name = 'courses/instructor_list.html'
    dept = None

    def dispatch(self, *args, **kwargs):
        self.dept = get_object_or_404(
            Department, slug=self.kwargs['dept_slug'].lower())
        return super(InstructorListView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        return Instructor.objects.filter(department=self.dept)

    def get_context_data(self, **kwargs):
        context = super(InstructorListView, self).get_context_data(**kwargs)
        context['department'] = self.dept
        return context


class InstructorDetailView(DetailView):
    context_object_name = 'instructor'
    template_name = 'courses/instructor_detail.html'
    instructor = None

    def get_object(self, queryset=None):
        self.instructor = get_object_or_404(Instructor,
                                            pk=self.kwargs['inst_pk'])
        return self.instructor

    def get_context_data(self, **kwargs):
        context = super(InstructorDetailView, self).get_context_data(**kwargs)

        # Get all course surveys for the instructor
        surveys = Survey.objects.filter(instructor=self.instructor)
        context['surveys'] = surveys

        # Get the average rating for the instructor and the ratings of all
        # courses taught
        course_instances = CourseInstance.objects.filter(
            instructors=self.instructor)
        courses = sorted(Course.objects.select_related('department').filter(
            courseinstance__in=course_instances).distinct())
        context['courses'] = courses
        context['total_prof_ratings_avg'] = surveys.aggregate(
            Avg('prof_rating'))['prof_rating__avg']
        # For each course that this instructor has taught, average the
        # prof_rating course_rating across the instructor's surveys for each
        # course, and put them in the dictionaries prof_ratings_avg and
        # course_ratings_avg  with key = course.abbreviation(),
        # value = avg_rating
        prof_ratings_avg = dict()
        course_ratings_avg = dict()
        for course in courses:
            ratings = surveys.filter(course=course).aggregate(
                Avg('prof_rating'), Avg('course_rating'))
            prof_ratings_avg[course.abbreviation()] = (
                ratings['prof_rating__avg'])
            course_ratings_avg[course.abbreviation()] = (
                ratings['course_rating__avg'])
        context['prof_ratings_avg'] = prof_ratings_avg
        context['course_ratings_avg'] = course_ratings_avg
        return context


class InstructorEditView(UpdateView):
    context_object_name = 'instructor'
    form_class = InstructorEditForm
    model = Instructor
    pk_url_kwarg = 'inst_pk'
    template_name = 'courses/edit_instructor.html'

    @method_decorator(login_required)
    @method_decorator(
        permission_required('courses.change_instructor', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        return super(InstructorEditView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'Changes saved!')
        return super(InstructorEditView, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct your input fields.')
        return super(InstructorEditView, self).form_invalid(form)


class InstructorDeleteView(DeleteView):
    context_object_name = 'instructor'
    model = Instructor
    pk_url_kwarg = 'inst_pk'
    template_name = 'courses/delete_instructor.html'
    dept_slug = None

    @method_decorator(login_required)
    @method_decorator(
        permission_required('courses.delete_instructor', raise_exception=True))
    def dispatch(self, *args, **kwargs):
        self.dept_slug = self.get_object().department.slug
        return super(InstructorDeleteView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'Instructor deleted!')
        return super(InstructorDeleteView, self).form_valid(form)

    def get_success_url(self):
        return reverse(
            'courses:instructor-list', kwargs={'dept_slug': self.dept_slug})
