# pylint: disable=W0402
import string

from django.db import models
from django.template.defaultfilters import slugify

from quark.base.models import Term


class Department(models.Model):
    long_name = models.CharField(
        max_length=100,
        help_text='Full name for department (e.g. Computer Science)')
    short_name = models.CharField(
        max_length=25,
        unique=True,
        help_text='Colloquial shorthand for department (e.g. CS)')
    abbreviation = models.CharField(
        max_length=25,
        help_text=('Standardized abbreviation for department from '
                   'the registrar (e.g. COMPSCI)'))
    slug = models.SlugField(
        max_length=25,
        editable=False)

    def __unicode__(self):
        return self.long_name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.short_name)
        self.abbreviation = self.abbreviation.upper().strip()
        super(Department, self).save(*args, **kwargs)


class Course(models.Model):
    department = models.ForeignKey(Department)
    number = models.CharField(max_length=10, db_index=True)
    title = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

    def __lt__(self, other):
        if not isinstance(other, Course):
            return False
        # Compare departments of courses
        if (self.department.abbreviation < other.department.abbreviation):
            return True
        elif (self.department.abbreviation > other.department.abbreviation):
            return False
        else:
            # Compare integer part of course numbers
            if (int(self.number.strip(string.letters)) <
                    int(other.number.strip(string.letters))):
                return True
            elif (int(self.number.strip(string.letters)) >
                    int(other.number.strip(string.letters))):
                return False
            else:
                # Compare postfix letters of course numbers
                if (self.number.lstrip(string.letters) <
                        other.number.lstrip(string.letters)):
                    return True
                elif (self.number.lstrip(string.letters) >
                        other.number.lstrip(string.letters)):
                    return False
                else:
                    # Compare prefix letters of the course numbers
                    return self.number < other.number

    def __le__(self, other):
        if not isinstance(other, Course):
            return False
        return not other.__lt__(self)

    def __eq__(self, other):
        if not isinstance(other, Course):
            return False
        return (self.number == other.number and
                self.department.id == other.department.id)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __gt__(self, other):
        if not isinstance(other, Course):
            return False
        return other.__lt__(self)

    def __ge__(self, other):
        if not isinstance(other, Course):
            return False
        return not self.__lt__(other)

    def __unicode__(self):
        return self.abbreviation()

    def abbreviation(self):
        return '%s %s' % (self.department.short_name, self.number)

    def save(self, *args, **kwargs):
        self.number = self.number.upper().strip()
        super(Course, self).save(*args, **kwargs)

    class Meta:
        unique_together = ('department', 'number')


class Instructor(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    department = models.ForeignKey(Department)
    website = models.URLField(blank=True)

    def __unicode__(self):
        return '%s (%s)' % (self.full_name(), self.department.short_name)

    def full_name(self):
        return '%s %s' % (self.first_name, self.last_name)

    class Meta:
        unique_together = ('first_name', 'last_name', 'department')


class CourseInstance(models.Model):
    term = models.ForeignKey(Term)
    course = models.ForeignKey(Course)
    instructors = models.ManyToManyField(Instructor)

    def __unicode__(self):
        return '%s - %s' % (self.course, self.term)
