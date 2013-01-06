import re

from django.db import models
from django.utils import timezone

from quark.auth.models import User
from quark.base.models import OfficerPosition
from quark.base.models import Term


class ProjectReport(models.Model):

    PROJECT_AREA_CHOICES = (
        ('cl', 'Community/Liberal Culture'),
        ('uc', 'University/College'),
        ('pe', 'Profession/Engineering'),
        ('cs', 'Chapter/Social'),
        ('ep', 'Education/Prof. Dev.'))

    term = models.ForeignKey(Term)
    date = models.DateField()
    title = models.CharField(max_length=80)
    author = models.ForeignKey(User)
    committee = models.ForeignKey(OfficerPosition)
    area = models.CharField(max_length=2, choices=PROJECT_AREA_CHOICES,
                            blank=True)
    organize_hours = models.PositiveSmallIntegerField(default=0)
    participate_hours = models.PositiveSmallIntegerField(default=0)
    location = models.CharField(max_length=100)
    is_new = models.BooleanField(default=False)
    other_group = models.CharField(max_length=60, blank=True)
    description = models.TextField(blank=True,
                                   help_text=('General description of event,'
                                              'vendors, sponsors, etc.'))
    purpose = models.TextField(blank=True)
    organization = models.TextField(blank=True,
                                    help_text=('Setup, number of people'
                                               'involved, clean-up, etc.'))
    cost = models.TextField(blank=True)
    problems = models.TextField(blank=True)
    results = models.TextField(blank=True)
    officer_list = models.ManyToManyField(User, related_name='officer_list+',
                                          blank=True)
    member_list = models.ManyToManyField(User, related_name='member_list+',
                                         blank=True)
    candidate_list = models.ManyToManyField(User,
                                            related_name='candidate_list+',
                                            blank=True)
    non_tbp = models.PositiveSmallIntegerField(default=0)
    complete = models.BooleanField(default=False)
    first_completed_at = models.DateTimeField(null=True, blank=True)
    attachment = models.FileField(upload_to='pr', blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '%s (%s)' % (self.title, self.date)

    def save(self, *args, **kwargs):
        if self.first_completed_at is None and self.complete:
            self.first_completed_at = timezone.now()
        elif not self.complete:
            self.first_completed_at = None
        super(ProjectReport, self).save(*args, **kwargs)

    def word_count(self):
        text = [self.description, self.purpose, self.organization, self.cost,
                self.problems, self.results]
        return len([x for x in re.split(r'\W+', ' '.join(text)) if len(x) > 0])

    # TODO(giovanni): Implement user_notification when UserNotification is up
