from django.conf import settings
from django.db import models

from quark.base.models import Term


class OfficerPosition(models.Model):
    """
    Available officer position in any of the quark-supported organizations.
    An Officer object would reference an instance of OfficerPosition to link a
    user to an officer position.
    """
    short_name = models.CharField(max_length=16, unique=True)
    long_name = models.CharField(max_length=64, unique=True)
    rank = models.DecimalField(max_digits=5, decimal_places=2)
    mailing_list = models.CharField(
        max_length=16, blank=True,
        help_text='The mailing list name, not including the @domain.')
    executive = models.BooleanField(
        default=False,
        help_text='Is this an executive position (like President)?')
    auxiliary = models.BooleanField(
        default=False,
        help_text='Is this position auxiliary (i.e., not a core officer '
                  'position)?')

    class Meta(object):
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
            self.user.get_username(), self.position.short_name,
            self.term.get_term_display(), self.term.year)

    def position_name(self):
        name = self.position.long_name
        if self.is_chair:
            name += ' Chair'
        return name

    class Meta(object):
        unique_together = ('user', 'position', 'term')
