from django.conf import settings
from django.db import models

from quark.base.models import Term


class OfficerPosition(models.Model):
    """
    Available officer position in any of the quark-supported organizations.
    An Officer object would reference an instance of OfficerPosition to link a
    user to an officer position.
    """
    # constants
    TBP_OFFICER = 0
    PIE_COORD = 1
    PIE_LEAD = 2
    PIE_STAFF = 3

    OFFICER_TYPE_CHOICES = (
        (TBP_OFFICER, 'TBP Officer'),
        (PIE_COORD, 'PiE Coordinator'),
        (PIE_LEAD, 'PiE Lead'),
        (PIE_STAFF, 'PiE Staff'),
    )

    position_type = models.PositiveSmallIntegerField(
        choices=OFFICER_TYPE_CHOICES)
    short_name = models.CharField(max_length=16, unique=True)
    long_name = models.CharField(max_length=64, unique=True)
    rank = models.DecimalField(max_digits=5, decimal_places=2)
    mailing_list = models.CharField(max_length=16, blank=True)

    class Meta:
        ordering = ('rank',)

    def __unicode__(self):
        return self.long_name

    def natural_key(self):
        return (self.short_name,)


class Officer(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    position = models.ForeignKey(OfficerPosition)
    term = models.ForeignKey(Term)

    is_chair = models.BooleanField(default=False)

    def __unicode__(self):
        return '%s - %s (%s %d)' % (
            self.user.username, self.position.short_name,
            self.term.get_term_display(), self.term.year)

    def position_name(self):
        name = self.position.long_name
        if self.is_chair:
            name += ' Chair'
        return name

    class Meta:
        unique_together = ('user', 'position', 'term')
