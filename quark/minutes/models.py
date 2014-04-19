import datetime

from django.conf import settings
from django.db import models

from quark.base.models import Term


class Minutes(models.Model):
    """Provides a way to store notes for meetings."""
    # constants
    OFFICER = 0
    EXEC = 1
    OTHER = 2

    MEETING_TYPES = (
        (OFFICER, 'Officer Meeting'),
        (EXEC, 'Executive Meeting'),
        (OTHER, 'Other'),
    )

    name = models.CharField(
        max_length=60, help_text='The name of the meeting.')
    date = models.DateField(
        default=datetime.date.today, help_text='Date the meeting was held.')
    term = models.ForeignKey(Term)
    meeting_type = models.PositiveSmallIntegerField(choices=MEETING_TYPES)
    notes = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta(object):
        ordering = ('-date',)
        permissions = (
            ('view_minutes', 'Can view all minutes'),
        )
        verbose_name = 'minutes'
        verbose_name_plural = 'minutes'

    def __unicode__(self):
        return '{0} {1:%Y-%m-%d %H:%M:%S}'.format(
            self.name, self.date)
