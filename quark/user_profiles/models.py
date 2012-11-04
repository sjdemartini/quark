from django.db import models
from django_localflavor_us.models import PhoneNumberField
from django_localflavor_us.models import USStateField
from filer.fields.image import FilerImageField

from quark.auth.models import User
from quark.base.models import IDCodeMixin
from quark.base.models import Major
from quark.base.models import Officer
from quark.base.models import OfficerPosition
from quark.base.models import Term
from quark.shortcuts import get_object_or_none


class CollegeStudentInfo(models.Model, IDCodeMixin):
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
        # pylint: disable=E1101
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
        # pylint: disable=E1101
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
        ordering = ['user']

    def __unicode__(self):
        # pylint: disable=E1101
        return self.user.get_common_name()

    def is_officer(self):
        """Returns true if this person has ever been an officer."""
        return Officer.objects.filter(user=self.user).exists()

    def is_current_officer(self, term=None, exclude_aux=False):
        """Returns True if this person is a current officer.

        Examines whether the person is an officer in the specified term, or the
        current term if no term specified. If exclude_aux is True, then
        auxiliary positions (specified below in this method) are not counted as
        officer positions.
        """
        if term is None:
            term = Term.objects.get_current_term()
        officer_positions = self.get_officer_positions(term)
        if officer_positions:
            if exclude_aux:
                excluded_positions = ['advisor', 'faculty']
                # House leaders considered as officers (not auxiliary) since
                # Fall 2012
                if term < Term.objects.get_or_create(term=Term.FALL,
                                                     year=2012):
                    excluded_positions.append('house-leader')

                officer_positions = [
                    position for position in officer_positions
                    if position.short_name not in excluded_positions]
                return len(officer_positions) > 0
            return True
        return False

    def get_all_officer_positions(self):
        """Returns a list of all officer positions held, past and present."""
        officers = Officer.objects.filter(user=self.user)
        return [officer.position for officer in officers]

    def get_officer_positions(self, term=None):
        """Returns a list of all officer positions in the specified term, or
        in the current term if no term specified."""
        if not term:
            term = Term.objects.get_current_term()
        officers = Officer.objects.filter(user=self.user, term=term)
        return [officer.position for officer in officers]

    # TODO(sjdemartini): implement is_candidate()
#    def is_candidate(self):
#        # avoid circular dependency
#        from candidate_portal.models import CandidateProfile
#        candidate = CandidateProfile.objects.filter(user=self.user)
#        return (len(candidate) > 0 and
#                Term.objects.get_current_term() <= candidate[0].term)

    def is_position(self, position):
        """Returns true if the person has ever held the input 'position'."""
        return Officer.objects.filter(
            user=self.user, position__short_name=position).exists()

    def get_preferred_email(self):
        """Returns the preferred email of this user.

        The order of preference is as follows:
        1. Officer @tbp email
        2. QuarkUser email
        3. UserContactInfo alt email address
        """
        if self.is_officer():
            # pylint: disable=E1101
            return '%s@tbp.berkeley.edu' % self.user.username
        contact_info = get_object_or_none(UserContactInfo, user=self.user)
        alt_email = contact_info.alt_email if contact_info else None
        # pylint: disable=E1101
        return self.user.email or alt_email


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
