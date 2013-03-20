from django.db import models
from django_localflavor_us.models import PhoneNumberField
from django_localflavor_us.models import USStateField
from filer.fields.image import FilerImageField

from quark.auth.models import User
from quark.base.models import IDCodeMixin
from quark.base.models import Major
from quark.base.models import Term


class CollegeStudentInfo(IDCodeMixin):
    GENDER_CHOICES = (
        ('F', 'Female'),
        ('M', 'Male'),
    )

    user = models.ForeignKey(User, unique=True)
    # Note that the student's University is encapsulated in the "major" field
    major = models.ForeignKey(Major, null=True)

    start_term = models.ForeignKey(Term, related_name='+', null=True,
                                   verbose_name='First term at this school')
    grad_term = models.ForeignKey(Term, related_name='+', null=True)

    birthday = models.DateField(null=True)

    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)

    def __unicode__(self):
        return '%s - %s (%s - %s) id: %s' % (
            self.user.username, self.major, self.start_term, self.grad_term,
            self.id_code)


class UserContactInfo(models.Model):
    user = models.ForeignKey(User, unique=True)

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

    def __unicode__(self):
        return self.user.get_common_name()


class TBPProfile(models.Model):
    user = models.ForeignKey(User, unique=True)

    initiation_term = models.ForeignKey(Term, related_name='+', null=True,
                                        verbose_name='Term initiated into TBP')
    has_initiated = models.BooleanField(default=False)

    bio = models.TextField(blank=True,
                           help_text='Bio is optional for candidates')

    picture = FilerImageField(related_name='profile_picture',
                              null=True, blank=True,
                              help_text='Picture is optional for candidates')

    class Meta:
        ordering = ('user',)

    def __unicode__(self):
        return self.user.get_common_name()

    # TODO(sjdemartini): implement is_candidate()
#    def is_candidate(self):
#        # avoid circular dependency
#        from candidate_portal.models import CandidateProfile
#        candidate = CandidateProfile.objects.filter(user=self.user)
#        return (len(candidate) > 0 and
#                Term.objects.get_current_term() <= candidate[0].term)


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
