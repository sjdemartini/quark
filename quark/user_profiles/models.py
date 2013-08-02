from django.conf import settings
from django.db import models
from django_localflavor_us.models import PhoneNumberField
from django_localflavor_us.models import USStateField
from filer.fields.image import FilerImageField

from quark.base.models import IDCodeMixin
from quark.base.models import Major
from quark.base.models import Term
from quark.candidates.models import Candidate


class CollegeStudentInfo(IDCodeMixin):
    GENDER_CHOICES = (
        ('F', 'Female'),
        ('M', 'Male'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, unique=True)
    # Note that the student's University is encapsulated in the "major" field
    major = models.ForeignKey(Major, null=True)

    start_term = models.ForeignKey(Term, related_name='+', null=True,
                                   verbose_name='First term at this school')
    grad_term = models.ForeignKey(Term, related_name='+', null=True)

    birthday = models.DateField(null=True)

    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)

    class Meta:
        verbose_name_plural = 'college student info'

    def __unicode__(self):
        return '%s - %s (%s - %s) id: %s' % (
            self.user.username, self.major, self.start_term, self.grad_term,
            self.id_code)


class UserContactInfo(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, unique=True)

    alt_email = models.EmailField(
        blank=True,
        help_text=('Preferably a non-edu email address '
                   '(e.g., @gmail.com, @yahoo.com)'))

    cell_phone = PhoneNumberField(blank=True)
    home_phone = PhoneNumberField(blank=True)
    receive_text = models.BooleanField(default=False)

    local_address1 = models.CharField(max_length=256)
    local_address2 = models.CharField(max_length=256, blank=True)
    local_city = models.CharField(max_length=128)
    local_state = USStateField()
    local_zip = models.CharField(max_length=10)

    # require either permanent address or international address
    perm_address1 = models.CharField(
        max_length=256, blank=True, verbose_name='Permanent Address 1')
    perm_address2 = models.CharField(
        max_length=256, blank=True, verbose_name='Permanent Address 2')
    perm_city = models.CharField(
        max_length=128, blank=True, verbose_name='Permanent City')
    perm_state = USStateField(
        blank=True, default='CA', verbose_name='Permanent State')
    perm_zip = models.CharField(
        max_length=10, blank=True, verbose_name='Permanent Zip Code')

    international_address = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'user contact info'

    def __unicode__(self):
        return self.user.get_common_name()


class TBPProfile(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, unique=True)

    initiation_term = models.ForeignKey(Term, related_name='+',
                                        blank=True, null=True,
                                        verbose_name='Term initiated into TBP')

    bio = models.TextField(blank=True,
                           help_text='Bio is optional for candidates')

    picture = FilerImageField(related_name='profile_picture',
                              null=True, blank=True,
                              help_text='Picture is optional for candidates')

    class Meta:
        ordering = ('user',)

    def __unicode__(self):
        return self.user.get_common_name()

    def is_candidate(self, current=True):
        """Returns True if this person is a candidate, False if initiated.

        If the current argument is True, then this method returns True if and
        only if the user is a candidate in the current term and has not yet
        initiated.

        Otherwise, the method looks at whether the person has been or is
        currently a candidate and whether they have initiated this term or in
        the past. If they they have been a candidate before and they have not
        initiated, then the method returns True.
        """
        current_term = Term.objects.get_current_term()
        if self.initiation_term and self.initiation_term <= current_term:
            return False

        # Note that when Candidate objects are marked as initiated, this is
        # recorded into the TBPProfile with a post_save in the candidates app,
        # so if they are not recorded as initiated in their profile
        # (i.e., initiation_term not None) and a Candidate object exists, they
        # are considered a candidate:
        if current:
            return Candidate.objects.filter(
                user=self.user, term=current_term).exists()
        return Candidate.objects.filter(user=self.user).exists()

    def get_first_term_as_candidate(self):
        """Returns the Term this user was first a candidate.

        The method returns None if the user was never recorded as a candidate.
        """
        # Reverse reference Candidate class:
        terms = Term.objects.filter(candidate__user=self.user)
        if terms.exists():
            return terms[0]
        # If not Candidate objects for the user, return their initiation term,
        # which is None if they did not initiate
        return self.initiation_term


def tbp_profile_post_save(sender, instance, created, **kwargs):
    """Ensures that UserContactInfo and CollegeStudentInfo objects exist for
    every user with a TBPProfile.

    Whenever a TBPProfile is saved, this callback performs a get_or_create() to
    ensure that there is a UserContactInfo and a CollegeStudentInfo profile
    with the saved User.
    """
    UserContactInfo.objects.get_or_create(user=instance.user)
    CollegeStudentInfo.objects.get_or_create(user=instance.user)
models.signals.post_save.connect(tbp_profile_post_save, sender=TBPProfile)
