from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django_localflavor_us.models import PhoneNumberField
from django_localflavor_us.models import USStateField
from filer.fields.image import FilerImageField

from quark.base.models import IDCodeMixin
from quark.base.models import Major
from quark.base.models import Term
from quark.candidates.models import Candidate
from quark.qldap import utils as ldap_utils
from quark.shortcuts import get_object_or_none


class UserProfile(models.Model):
    """Basic user information."""
    GENDER_CHOICES = (
        ('F', 'Female'),
        ('M', 'Male'),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL)

    preferred_name = models.CharField(
        max_length=64,
        db_index=True,
        blank=True,
        help_text='What would you like us to call you? (Optional)')

    middle_name = models.CharField(max_length=64, blank=True)
    birthday = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)

    picture = FilerImageField(related_name='profile_picture',
                              blank=True, null=True,
                              help_text='Optional')

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.get_common_name()

    def get_short_name(self):
        return self.preferred_name or self.user.first_name

    def get_full_name(self):
        if self.middle_name:
            return '{0} {1} {2}'.format(
                self.user.first_name, self.middle_name, self.user.last_name)
        else:
            return '{} {}'.format(self.user.first_name, self.user.last_name)

    def get_common_name(self):
        return '{} {}'.format(self.get_short_name(), self.user.last_name)

    def get_college_student_info(self):
        return get_object_or_none(CollegeStudentInfo, user=self.user)

    def get_contact_info(self):
        return get_object_or_none(UserContactInfo, user=self.user)

    def get_student_org_user_profile(self):
        return get_object_or_none(StudentOrgUserProfile, user=self.user)

    def get_preferred_email(self):
        """Return the preferred email address of this user.

        The order of preference is as follows:
        1. Officer email (if user is an officer of their organization)
        2. User email
        3. UserContactInfo alt email address
        """
        if self.is_officer() and hasattr(settings, 'HOSTNAME'):
            return '{}@{}'.format(self.user.username, settings.HOSTNAME)

        if self.user.email:
            return self.user.email

        contact_info = self.get_contact_info()
        return contact_info.alt_email if contact_info else None

    # The following methods pertain to the user's student organization, and
    # they are included as methods of the UserProfile for performance reasons,
    # as they can be accessed easily, given that UserProfile is OneToOne with
    # the user model.

    def is_candidate(self, current=True):
        """Return True if this person is a candidate, False if initiated.

        This method simply calls the StudentOrgUserProfile method is_candidate,
        or returns False if no StudentOrgUserProfile exists for this user.
        """
        profile = self.get_student_org_user_profile()
        return profile.is_candidate() if profile else False

    def is_member(self):
        """Return true if this person is a member of the organization."""
        # TODO(sjdemartini): Gate all LDAP operations behind a setting, so
        # that LDAP is only used if settings have LDAP enabled.
        return (self.is_officer() or
                ldap_utils.is_in_tbp_group(self.username, 'members'))

    def is_officer(self, current=False, exclude_aux=False):
        """Return True if this person is an officer in the organization.

        If current=False, then the method returns True iff the person has ever
        been an officer. If current=True, then the method returns True iff
        the person is currently an officer.

        If exclude_aux is True, then auxiliary positions (specified below in
        this method) are not counted as officer positions.
        """
        if current:
            term = Term.objects.get_current_term()
        else:
            # If registered as an officer in LDAP, then return true
            # TODO(sjdemartini): Gate all LDAP operations behind a setting, so
            # that LDAP is only used if settings have LDAP enabled.
            if (not exclude_aux and
                    ldap_utils.is_in_tbp_group(
                    self.user.username, 'officers')):
                return True
            term = None
        officer_positions = self.get_officer_positions(term)
        if officer_positions:
            if exclude_aux:
                excluded_positions = set(['advisor', 'faculty'])
                for position in officer_positions:
                    if position.short_name not in excluded_positions:
                        return True
            else:
                return True
        return False

    def get_officer_positions(self, term=None):
        """Return a list of all officer positions held by this user in the
        specified term, or in all terms if no term specified.

        The order of the list is from oldest to newest term, and within a term,
        from highest rank OfficerPosition (smallest number) to lowest rank.
        """
        # Note that QuerySets are lazy, so there is no database activity until
        # the list comprehension
        # Import OfficerPosition here to avoid circular dependency
        from quark.base_tbp.models import OfficerPosition
        officers = self.user.officer_set.filter(
            position__position_type=OfficerPosition.TBP_OFFICER).order_by(
            'term', 'position')
        if term:
            officers = officers.filter(term=term)
        return [officer.position for officer in officers]

    def is_officer_position(self, position, current=False):
        """Return True if the person has held this position.

        If current=False, then the method returns True iff the person has ever
        held the position. If current=True, then the method returns True iff
        the person currently holds the position.
        """
        officers = self.user.officer_set.filter(position__short_name=position)
        if current:
            officers = officers.filter(term=Term.objects.get_current_term())
        return officers.exists()


class CollegeStudentInfo(IDCodeMixin):
    """Information about a college student user."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, unique=True)
    # Note that the student's University is encapsulated in the "major" field
    major = models.ForeignKey(Major, null=True)

    start_term = models.ForeignKey(Term, related_name='+', null=True,
                                   verbose_name='First term at this school')
    grad_term = models.ForeignKey(Term, related_name='+', null=True,
                                  verbose_name='Graduation term')

    class Meta(object):
        verbose_name_plural = 'college student info'

    def __unicode__(self):
        return '%s - %s (%s - %s) id: %s' % (
            self.user.username, self.major, self.start_term, self.grad_term,
            self.id_code)


class UserContactInfo(models.Model):
    """Contact information for a user."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, unique=True)

    alt_email = models.EmailField(
        blank=True,
        help_text=('Preferably a non-edu email address '
                   '(e.g., @gmail.com, @yahoo.com)'))

    cell_phone = PhoneNumberField(blank=True)
    home_phone = PhoneNumberField(blank=True)
    receive_text = models.BooleanField(
        default=False,
        help_text='Can you send and receive text messages on your cell phone?')

    local_address1 = models.CharField(max_length=256, blank=True)
    local_address2 = models.CharField(max_length=256, blank=True)
    local_city = models.CharField(max_length=128, blank=True)
    local_state = USStateField(blank=True)
    local_zip = models.CharField(max_length=10, blank=True)

    # Require either permanent address or international address
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

    class Meta(object):
        verbose_name_plural = 'user contact info'

    def __unicode__(self):
        return self.user.get_full_name()


class StudentOrgUserProfile(models.Model):
    """A user's information specific to the student organization."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, unique=True)

    initiation_term = models.ForeignKey(
        Term, related_name='+', blank=True, null=True,
        verbose_name='Term initiated into the organization.')

    bio = models.TextField(
        blank=True, help_text='Bio is optional for candidates')

    class Meta(object):
        ordering = ('user',)
        verbose_name = 'Student Organization User Profile'

    def __unicode__(self):
        return self.user.get_full_name()

    def is_candidate(self, current=True):
        """Return True if this person is a candidate, False if initiated.

        If the 'current' argument is True, then this method returns True if and
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
        # recorded into the StudentOrgUserProfile with a post_save in the
        # candidates app, so if they are not recorded as initiated in their
        # profile (i.e., initiation_term not None) and a Candidate object
        # exists, they are considered a candidate:
        if current:
            return Candidate.objects.filter(
                user=self.user, term=current_term).exists()
        return Candidate.objects.filter(user=self.user).exists()

    def get_first_term_as_candidate(self):
        """Return the Term this user was first a candidate.

        The method returns None if the user was never recorded as a candidate.
        """
        # Reverse reference Candidate class:
        terms = Term.objects.filter(candidate__user=self.user)
        if terms.exists():
            return terms[0]
        # If not Candidate objects for the user, return their initiation term,
        # which is None if they did not initiate
        return self.initiation_term


def user_profile_post_save(sender, instance, created, **kwargs):
    """Ensures that a UserProfile object exists for every user.

    Whenever a user is created, this callback performs a get_or_create()
    to ensure that there is a UserProfile for the saved User.
    """
    if created:
        UserProfile.objects.get_or_create(user=instance)


def student_org_user_profile_post_save(sender, instance, created, **kwargs):
    """Ensures that UserContactInfo and CollegeStudentInfo objects exist for
    every user with a StudentOrgUserProfile.

    Whenever a StudentOrgUserProfile is created, this callback performs a
    get_or_create() to ensure that there is a UserContactInfo and a
    CollegeStudentInfo for the saved User.
    """
    if created:
        UserContactInfo.objects.get_or_create(user=instance.user)
        CollegeStudentInfo.objects.get_or_create(user=instance.user)


models.signals.post_save.connect(
    user_profile_post_save, sender=get_user_model())

models.signals.post_save.connect(
    student_org_user_profile_post_save, sender=StudentOrgUserProfile)
