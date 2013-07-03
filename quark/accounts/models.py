from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone

from quark.qldap import utils as ldap_utils


class QuarkUserManager(BaseUserManager):
    def create_user(self, username, email, password,
                    first_name, last_name, **extra_fields):
        # Password must not be empty, but can be None for unusuable password
        if ((not username or not email or password == '' or
             not first_name or not last_name)):
            raise ValueError('Users must have username, email, password, '
                             'first name and last name')

        user = self.model(
            username=username,
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            **extra_fields)

        # Providing password=None is equivalent to set_unusable_password
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, email, password,
                         first_name, last_name, **extra_fields):
        return self.create_user(username, email, password,
                                first_name, last_name,
                                is_superuser=True, **extra_fields)


class QuarkUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=30, unique=True)
    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name='email address')
    # Names
    first_name = models.CharField(
        max_length=64,
        db_index=True,
        help_text='Your official first or given name')
    middle_name = models.CharField(max_length=64, blank=True)
    last_name = models.CharField(max_length=64, db_index=True)
    # Note that preferred_name is pulled from first_name in the save() method
    # if preferred_name is left blank
    preferred_name = models.CharField(
        max_length=64,
        db_index=True,
        blank=True,
        help_text='What would you like us to call you? (Optional)')

    created = models.DateTimeField(default=timezone.now)

    objects = QuarkUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Quark User'
        ordering = ('last_name', 'preferred_name',)

    def __unicode__(self):
        return '{} ({})'.format(self.username, self.get_full_name())

    def save(self, *args, **kwargs):
        if not self.preferred_name:
            self.preferred_name = self.first_name
        super(QuarkUser, self).save(*args, **kwargs)

    def get_full_name(self):
        if self.middle_name:
            return '{0} {1} {2}'.format(
                self.first_name, self.middle_name, self.last_name)
        else:
            return '{} {}'.format(self.first_name, self.last_name)

    def get_common_name(self):
        return '{} {}'.format(self.preferred_name, self.last_name)

    def get_short_name(self):
        return self.preferred_name or self.first_name

    @property
    def is_staff(self):
        # TODO(flieee): True if user is in some sort of IT role also
        return self.is_superuser

    def is_tbp_member(self):
        """Returns true if this person is a TBP member."""
        return (self.is_tbp_officer() or
                ldap_utils.is_in_tbp_group(self.username, 'members'))

    def is_tbp_candidate(self, current=True):
        """Returns True if this person is a candidate, False if initiated.

        This method simply calls the TBPProfile method is_candidate, or returns
        False if no TBPProfile exists for this user.
        """
        profile = self.tbpprofile_set
        # TBPProfile is unique to each User, so if it exists, call get()
        # to access it:
        return profile.get().is_candidate() if profile.exists() else False

    def is_tbp_officer(self, current=False, exclude_aux=False):
        """Returns True if this person is a TBP officer.

        If current=False, then the method returns True iff the person has ever
        been an officer. If current=True, then the method returns True iff
        the person is currently an officer.

        If exclude_aux is True, then auxiliary positions (specified below in
        this method) are not counted as officer positions.
        """
        if current:
            # Import Term here to avoid circular dependency
            from quark.base.models import Term
            term = Term.objects.get_current_term()
        else:
            # If registered as an officer in LDAP, then return true
            if (not exclude_aux and
                    ldap_utils.is_in_tbp_group(self.username, 'officers')):
                return True
            term = None
        officer_positions = self.get_tbp_officer_positions(term)
        if officer_positions:
            if exclude_aux:
                excluded_positions = set(['advisor', 'faculty'])
                officer_positions = [
                    position for position in officer_positions
                    if position.short_name not in excluded_positions]
                return len(officer_positions) > 0
            else:
                return True
        return False

    def get_tbp_officer_positions(self, term=None):
        """Returns a list of all officer positions held by this user in the
        specified term, or in all terms if no term specified.

        The order of the list is from oldest to newest term, and within a term,
        from highest rank OfficerPosition (smallest number) to lowest rank.
        """
        # Note that QuerySets are lazy, so there is no database activity until
        # the list comprehension
        # Import OfficerPosition here to avoid circular dependency
        from quark.base_tbp.models import OfficerPosition
        officers = self.officer_set.filter(
            position__position_type=OfficerPosition.TBP_OFFICER).order_by(
                'term', 'position')
        if term:
            officers = officers.filter(term=term)
        return [officer.position for officer in officers]

    def is_tbp_position(self, position, current=False):
        """Returns True if the person has held this position.

        If current=False, then the method returns True iff the person has ever
        held the position. If current=True, then the method returns True iff
        the person currently holds the position.
        """
        officers = self.officer_set.filter(position__short_name=position)
        if current:
            # Import Term here to avoid circular dependency
            from quark.base.models import Term
            officers = officers.filter(term=Term.objects.get_current_term())
        return officers.exists()

    def get_preferred_email(self):
        """Returns the preferred email of this user.

        The order of preference is as follows:
        1. Officer @tbp email (if user is a TBP officer)
        2. User email
        3. UserContactInfo alt email address
        """
        if self.is_tbp_officer():
            return '{}@tbp.berkeley.edu'.format(self.username)
        contact_info = self.usercontactinfo_set
        # UserContactInfo is unique to each User, so if it exists, call get()
        # to access it:
        alt_email = (contact_info.get().alt_email if contact_info.exists()
                     else None)
        return self.email or alt_email


class LDAPQuarkUserManager(QuarkUserManager):
    """
    Creates LDAP entries for users when creating users
    """
    def create_user(self, username, email, password,
                    first_name, last_name, **extra_fields):
        norm_email = self.normalize_email(email)
        if ldap_utils.create_user(username, password, norm_email,
                                  first_name, last_name):
            # Create a QuarkUser with an unusable password (None)
            return super(LDAPQuarkUserManager, self).create_user(
                username, email, password,
                first_name, last_name, **extra_fields)
        else:
            # Failed to create a new user entry in LDAP
            return None

    def create_superuser(self, username, email, password,
                         first_name, last_name, **extra_fields):
        norm_email = self.normalize_email(email)
        if ldap_utils.create_user(username, password, norm_email,
                                  first_name, last_name):
            # Create a QuarkUser with an unusable password (None)
            return super(LDAPQuarkUserManager, self).create_superuser(
                username, email, password,
                first_name, last_name, **extra_fields)
        else:
            # Failed to create a new user entry in LDAP
            return None


class LDAPQuarkUser(QuarkUser):
    """
    Overrides default custom user's password facilities.
    TODO(flieee): Also synchronizes username with LDAP on save
    Requires quark.qldap
    """
    objects = LDAPQuarkUserManager()

    class Meta:
        proxy = True
        verbose_name = 'LDAP Quark User'

    def save(self, *args, **kwargs):
        """Only save the instance if user exists in LDAP"""
        if ldap_utils.username_exists(self.username):
            super(LDAPQuarkUser, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Only delete the instance if LDAP user deletion was successfull"""
        if ldap_utils.delete_user(self.username):
            super(LDAPQuarkUser, self).save(*args, **kwargs)

    def check_password(self, raw_password):
        return ldap_utils.check_password(self.username, raw_password)

    def set_password(self, raw_password):
        self.set_unusable_password()
        ldap_utils.set_password(self.username, raw_password)


class CompanyUserManager(BaseUserManager):
    def create_user(self, username, email, password,
                    company_name, **extra_fields):
        # Password must not be empty, but can be None for unusuable password
        if not username or not email or password == '' or not company_name:
            raise ValueError('Users must have username, email, password, '
                             'and company name')

        user = self.model(
            username=username,
            email=self.normalize_email(email),
            company_name=company_name,
            **extra_fields)

        # Providing password=None is equivalent to set_unusable_password
        user.set_password(password)
        user.save()
        return user


class CompanyQuarkUser(AbstractBaseUser, PermissionsMixin):
    """An account for companies and industry contacts to use to log in and
    access features such as the resume bank, request infosessions, etc."""
    username = models.CharField(max_length=30, unique=True)
    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name='Contact email address')
    company_name = models.CharField(
        max_length=64,
        db_index=True,
        help_text='Your company\'s name')

    created = models.DateTimeField(default=timezone.now)

    objects = CompanyUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'company_name']

    class Meta:
        verbose_name = 'Company User'
        ordering = ('company_name',)

    def __unicode__(self):
        return '{} ({})'.format(self.username, self.company_name)

    def get_full_name(self):
        return self.company_name

    def get_short_name(self):
        return self.company_name

    @property
    def is_staff(self):
        return False
