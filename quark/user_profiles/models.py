import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from localflavor.us.models import PhoneNumberField
from localflavor.us.models import USStateField

from quark.base.models import IDCodeMixin
from quark.base.models import Major
from quark.base.models import Officer
from quark.base.models import OfficerPosition
from quark.base.models import Term
from quark.candidates.models import Candidate
from quark.qldap import utils as ldap_utils
from quark.shortcuts import disable_for_loaddata


USE_LDAP = getattr(settings, 'USE_LDAP', False)


class UserProfile(models.Model):
    """Basic user information."""
    GENDER_CHOICES = (
        ('F', 'Female'),
        ('M', 'Male'),
    )

    PICTURES_LOCATION = 'user_profiles'

    def rename_file(instance, filename):
        """Rename the file to the user's username, and update the file if it
        already exists.
        """
        # pylint: disable=E0213
        file_ext = os.path.splitext(filename)[1]
        filename = os.path.join(UserProfile.PICTURES_LOCATION,
                                str(instance.user.get_username()) + file_ext)
        full_path = os.path.join(settings.MEDIA_ROOT, filename)
        # if the file already exists, delete it so the new file can
        # use the same name
        if os.path.exists(full_path):
            os.remove(full_path)
        return filename

    user = models.OneToOneField(settings.AUTH_USER_MODEL)

    # Note that preferred_name is pulled from the user's first_name in the
    # save() method if preferred_name is left blank
    preferred_name = models.CharField(
        max_length=64,
        db_index=True,
        blank=True,
        help_text='What would you like us to call you?')

    middle_name = models.CharField(max_length=64, blank=True)
    birthday = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)

    picture = models.ImageField(upload_to=rename_file, blank=True, null=True)

    alt_email = models.EmailField(
        blank=True,
        verbose_name='Alternate email address',
        help_text=('Preferably at least one of your email addresses on record '
                   'will be a non-edu address (e.g., @gmail.com, @yahoo.com).'))

    cell_phone = PhoneNumberField(blank=True)
    home_phone = PhoneNumberField(blank=True)
    receive_text = models.BooleanField(
        default=False,
        help_text='Can you send and receive text messages on your cell phone?')

    local_address1 = models.CharField(
        max_length=256, blank=True, verbose_name='Local Address Line 1')
    local_address2 = models.CharField(
        max_length=256, blank=True, verbose_name='Local Address Line 2')
    local_city = models.CharField(max_length=128, blank=True)
    local_state = USStateField(blank=True)
    local_zip = models.CharField(
        max_length=10, blank=True, verbose_name='Local ZIP')

    perm_address1 = models.CharField(
        max_length=256, blank=True, verbose_name='Permanent Address Line 1')
    perm_address2 = models.CharField(
        max_length=256, blank=True, verbose_name='Permanent Address Line 2')
    perm_city = models.CharField(
        max_length=128, blank=True, verbose_name='Permanent City')
    perm_state = USStateField(
        default='CA', blank=True, verbose_name='Permanent State')
    perm_zip = models.CharField(
        max_length=10, blank=True, verbose_name='Permanent ZIP')

    international_address = models.TextField(blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta(object):
        ordering = ('preferred_name', 'user__last_name')

    def save(self, *args, **kwargs):
        """Ensure that the user has a preferred name saved.

        Cache the user's first name as their preferred name if the preferred
        name is not specified. This helps to ensure that we can sort users
        by their preferred_names, and also simplifies logic for displaying a
        user's "common" name.
        """
        if not self.preferred_name:
            self.preferred_name = self.user.first_name
        super(UserProfile, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.get_common_name()

    def get_verbose_first_name(self):
        """Return a verbose representation of the user's first name.

        The result includes both the preferred name and official first name, if
        they differ. For instance, if someone's first name is Robert, with the
        preferred name Bob, this method returns:
        Bob (Robert)
        """
        if self.preferred_name != self.user.first_name:
            # Use both "first" names
            return '{} ({})'.format(self.preferred_name, self.user.first_name)
        else:
            return self.user.first_name

    def get_full_name(self, include_middle_name=True, verbose=False):
        """Return the user's full name.

        If "include_middle_name" (default True) is True, the result includes
        the user's middle name if the user has one.

        If "verbose" (default False) is True, the result uses the verbose first
        name as the first name (see get_verbose_first_name). For instance, if
        someone's name is Robert Tau Bent, with the preferred name Bob, this
        method returns the following when verbose and include_middle_name are
        True:
        Bob (Robert) Tau Bent
        """
        if verbose:
            first_name = self.get_verbose_first_name()
        else:
            first_name = self.user.first_name

        if include_middle_name and self.middle_name:
            return '{0} {1} {2}'.format(
                first_name, self.middle_name, self.user.last_name)
        else:
            return '{} {}'.format(first_name, self.user.last_name)

    def get_verbose_full_name(self):
        """Return a verbose representation of the user's full name.

        Calls the get_full_name method with verbose set to True. Useful for
        usage in templates.
        """
        return self.get_full_name(verbose=True)

    def get_common_name(self):
        """Return the common representation of the person's name."""
        return '{} {}'.format(self.preferred_name, self.user.last_name)

    def get_public_name(self):
        """Return a version of a person's name to be visible publicly, with
        short name followed by last name initial.
        """
        return '{} {}.'.format(self.preferred_name, self.user.last_name[0])

    def get_college_student_info(self):
        try:
            return self.user.collegestudentinfo
        except CollegeStudentInfo.DoesNotExist:
            return None

    def get_student_org_user_profile(self):
        try:
            return self.user.studentorguserprofile
        except StudentOrgUserProfile.DoesNotExist:
            return None

    def get_preferred_email(self):
        """Return the preferred email address of this user.

        The order of preference is as follows:
        1. Officer email (if user is an officer of their organization)
        2. User email
        3. UserProfile alt email address
        """
        if self.is_officer() and hasattr(settings, 'HOSTNAME'):
            return '{}@{}'.format(self.user.get_username(), settings.HOSTNAME)

        return self.user.email or self.alt_email or None

    # The following methods pertain to the user's student organization, and
    # they are included as methods of the UserProfile for convenience reasons,
    # as they can be accessed easily.

    def is_candidate(self, current=True):
        """Return True if this person is a candidate, False if initiated.

        This method simply calls the StudentOrgUserProfile method is_candidate,
        or returns False if no StudentOrgUserProfile exists for this user.
        """
        profile = self.get_student_org_user_profile()
        return profile.is_candidate() if profile else False

    def is_member(self):
        """Return true if this person is a member of the organization."""
        profile = self.get_student_org_user_profile()
        return profile.is_member() if profile else False

    def is_officer(self, current=False, exclude_aux=False):
        """Return True if this person is an officer in the organization.
        """
        profile = self.get_student_org_user_profile()
        if profile:
            return profile.is_officer(current=current, exclude_aux=exclude_aux)
        else:
            return False


class CollegeStudentInfo(IDCodeMixin):
    """Information about a college student user."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL)
    # Note that the student's University is encapsulated in the "major" field
    major = models.ManyToManyField(Major, null=True)

    start_term = models.ForeignKey(Term, related_name='+', null=True,
                                   verbose_name='First term at this school')
    grad_term = models.ForeignKey(Term, related_name='+', null=True,
                                  verbose_name='Graduation term')

    class Meta(object):
        verbose_name_plural = 'college student info'

    def __unicode__(self):
        return '{username} ({start_term} - {grad_term}) id: {id_code}'.format(
            username=self.user.get_username(), start_term=self.start_term,
            grad_term=self.grad_term, id_code=self.id_code or None)


class StudentOrgUserProfile(models.Model):
    """A user's information specific to the student organization."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL)

    initiation_term = models.ForeignKey(
        Term, related_name='+', blank=True, null=True,
        verbose_name='Term initiated into the organization.')

    bio = models.TextField(blank=True)

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

    def is_member(self):
        """Return True if this person is a current member of the organization.

        Member status is indicated by having initiated, or by being an officer,
        or by being in the LDAP member database (if LDAP is enabled).
        """
        if self.initiation_term is not None:
            return True

        is_officer = self.is_officer()
        if USE_LDAP:
            is_ldap_member = ldap_utils.is_in_tbp_group(
                self.user.get_username(), 'members')
            return is_officer or is_ldap_member
        return is_officer

    def is_officer(self, current=False, exclude_aux=False):
        """Return True if this person is an officer in the organization.

        If current=False, then the method returns True iff the person has ever
        been an officer. If current=True, then the method returns True iff
        the person is currently an officer.

        If exclude_aux is True, then auxiliary positions (positions with
        auxiliary=True) are not counted as officer positions.
        """
        if current:
            term = Term.objects.get_current_term()
        else:
            # If registered as an officer in LDAP (and we don't need to exclude
            # auxiliary positions), then return true
            if (USE_LDAP and not exclude_aux and
                    ldap_utils.is_in_tbp_group(
                        self.user.get_username(), 'officers')):
                return True
            term = None
        officer_positions = self.get_officer_positions(term)
        if exclude_aux:
            officer_positions = officer_positions.exclude(auxiliary=True)
        return officer_positions.exists()

    def get_officer_positions(self, term=None):
        """Return a query set of all officer positions held by this user in the
        specified term, or in all terms if no term specified.

        The order of the list is from oldest to newest term, and within a term,
        from highest rank OfficerPosition (smallest number) to lowest rank.
        """
        if term:
            officer_positions = OfficerPosition.objects.filter(
                officer__user=self.user, officer__term=term)
        else:
            officer_positions = OfficerPosition.objects.filter(
                officer__user=self.user)

        return officer_positions.order_by('officer__term', 'rank')

    def is_officer_position(self, position, current=False):
        """Return True if the person has held this position.

        If current=False, then the method returns True iff the person has ever
        held the position. If current=True, then the method returns True iff
        the person holds the position in the current term.
        """
        officers = self.user.officer_set.filter(position__short_name=position)
        if current:
            officers = officers.filter(term=Term.objects.get_current_term())
        return officers.exists()

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


@disable_for_loaddata
def user_profile_creation_post_save(sender, instance, created, **kwargs):
    """Ensures that a UserProfile object exists for every user.

    Whenever a user is created, this callback performs a get_or_create()
    to ensure that there is a UserProfile for the saved User.
    """
    profile, _ = UserProfile.objects.get_or_create(user=instance)

    # If the profile does not have the preferred_name set and the user's
    # first_name field is not empty, call the profile's save method to update
    # the preferred_name field. This is necessary in case the profile was
    # originally created on post_save when the user's first_name was not
    # specified.
    if instance.first_name and not profile.preferred_name:
        profile.save()


def student_org_creation_post_save(sender, instance, created, **kwargs):
    """Ensure that StudentOrgUserProfiles exist when the sender is created.

    Useful for ensuring a StudentOrgUserProfile exists for every Officer.
    """
    if created:
        StudentOrgUserProfile.objects.get_or_create(user=instance.user)


def student_org_user_profile_post_save(sender, instance, created, **kwargs):
    """Ensure that CollegeStudentInfo objects exist for every user with a
    StudentOrgUserProfile.

    Whenever a StudentOrgUserProfile is created, this callback performs a
    get_or_create() to ensure that there is a CollegeStudentInfo object for the
    user.
    """
    if created:
        CollegeStudentInfo.objects.get_or_create(user=instance.user)


models.signals.post_save.connect(
    user_profile_creation_post_save, sender=get_user_model())

models.signals.post_save.connect(
    student_org_creation_post_save, sender=Officer)

models.signals.post_save.connect(
    student_org_user_profile_post_save, sender=StudentOrgUserProfile)
