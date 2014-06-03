import datetime

from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models


class Company(models.Model):
    """A model representing a Company with which the student organization has a
    relationship.

    A Company may have representatives (CompanyReps) who have accounts to log
    in on the website.
    """
    name = models.CharField(max_length=255, unique=True,
                            help_text='The name of the company.')

    website = models.URLField(max_length=255, blank=True,
                              help_text='The company website.')

    logo = models.ImageField(upload_to='company_logos/', blank=True,
                             help_text='The company logo.')

    expiration_date = models.DateField(
        help_text='The date the company account subscription expires.')

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta(object):
        verbose_name_plural = 'companies'
        permissions = (
            ('view_companies', 'Can view information about companies'),
        )

    def __unicode__(self):
        return self.name

    def is_expired(self):
        """Return True if this Company's account has expired.

        If the current date is past the expiration_date for this Company, then
        the account is considered to be expired. Associated CompanyRep users
        should no longer be allowed to log in.
        """
        return self.expiration_date < datetime.date.today()


class CompanyRep(models.Model):
    """A representative for a Company, who has an account on the site."""
    company = models.ForeignKey(
        Company,
        help_text='The Company this contact is associated with.')

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        help_text='The user account for this company contact')

    class Meta(object):
        permissions = (
            ('view_companyreps', 'Can view information about company reps'),
        )

    def __unicode__(self):
        return '{} ({})'.format(self.user, self.company.name)


def company_rep_post_save(sender, instance, created, **kwargs):
    company_rep_group = Group.objects.get(name='Company Representative')
    instance.user.groups.add(company_rep_group)

models.signals.post_save.connect(company_rep_post_save, sender=CompanyRep)
