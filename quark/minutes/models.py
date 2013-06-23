from datetime import datetime

from django.conf import settings
from django.db import models

from quark.base.models import Term


class Minutes(models.Model):
    """Provides a way to store notes for meetings."""
    # constants
    OM = 0
    EM = 1
    OTHER = 2
    MEETING_TYPES = (
        (OM, 'Officer Meeting'),
        (EM, 'Executive Meeting'),
        (OTHER, 'Other'),
    )
    name = models.CharField(max_length=60)
    date = models.DateTimeField(default=datetime.now)
    term = models.ForeignKey(Term)
    meeting_type = models.PositiveSmallIntegerField(choices=MEETING_TYPES)
    notes = models.TextField()
    public = models.BooleanField(default=False)
    author = models.ForeignKey(settings.AUTH_USER_MODEL)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-date',)
        permissions = (
            ('view_minutes', 'Can view all minutes'),
        )
        verbose_name = 'minutes'
        verbose_name_plural = 'minutes'

    def __unicode__(self):
        return '{0} {1:%Y-%m-%d %H:%M:%S}'.format(
            self.name, self.date)
