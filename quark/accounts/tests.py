import datetime
import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as DefaultUser
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.test.utils import override_settings
from mock import patch

from quark.accounts.forms import AuthenticationForm
from quark.accounts.models import make_ldap_user
from quark.accounts.models import LDAPUser
from quark.companies.models import Company
from quark.companies.models import CompanyRep
from quark.qldap.utils import delete_user
from quark.qldap.utils import get_email
from quark.qldap.utils import username_exists


class UserModelTest(TestCase):
    @override_settings(AUTH_USER_MODEL='auth.User')
    def get_correct_user_model(self):
        self.assertEqual(get_user_model(), DefaultUser)

    @override_settings(AUTH_USER_MODEL='nonexistent.User')
    def get_wrong_user_model(self):
        self.assertRaises(NameError, get_user_model)


@override_settings(AUTH_USER_MODEL='auth.User')
class CreateLDAPUserTestCase(TestCase):
    def setUp(self):
        self.model = LDAPUser
        # Use unique name for LDAP. Note that os.getpid is used to ensure that
        # we get a unique number for this test (rather than simply random),
        # as uniqueness is necessary for running the LDAP tests.
        rnd = os.getpid()
        self.username = 'testuser%d' % rnd
        self.email = 'test%d@tbp.berkeley.edu' % rnd
        self.password = 'testpassword'
        self.first_name = 'Mike'
        self.last_name = 'McTest'

    def tearDown(self):
        if username_exists(self.username):
            self.assertTrue(delete_user(self.username))

    def test_correct_user_model(self):
        """Make sure this test is using the proper model"""
        self.assertEqual(self.model, LDAPUser)

    def test_create_user(self):
        """Test creating a user."""
        if username_exists(self.username):
            self.assertTrue(delete_user(self.username))

        self.assertFalse(
            self.model.objects.filter(username=self.username).exists())
        self.assertIsNotNone(self.model.objects.create_user(
            username=self.username,
            email=self.email,
            password=self.password,
            first_name=self.first_name,
            last_name=self.last_name))

        self.verify_user_attributes_valid()

    def test_direct_create_user(self):
        """Creating an LDAP user directly via model instantiation."""
        if username_exists(self.username):
            self.assertTrue(delete_user(self.username))
        user = self.model(
            username=self.username,
            email=self.email,
            password=self.password,
            first_name=self.first_name,
            last_name=self.last_name)
        user.save()

        self.verify_user_attributes_valid()

    def test_create_incomplete_user(self):
        """Creating an LDAP user with incomplete information should raise a
        ValidationError.
        """
        if username_exists(self.username):
            self.assertTrue(delete_user(self.username))
        # Lacking first_name, last_name
        user = self.model(
            username=self.username,
            email=self.email,
            password=self.password)
        self.assertRaises(ValidationError, user.save)

        self.assertFalse(
            self.model.objects.filter(username=self.username).exists())
        self.assertFalse(username_exists(self.username))

    def test_create_superuser(self):
        """Test creating a superuser."""
        if username_exists(self.username):
            self.assertTrue(delete_user(self.username))

        self.assertFalse(
            self.model.objects.filter(username=self.username).exists())

        self.assertIsNotNone(self.model.objects.create_superuser(
            username=self.username,
            email=self.email,
            password=self.password,
            first_name=self.first_name,
            last_name=self.last_name))

        self.verify_user_attributes_valid(is_superuser=True)

    def verify_user_attributes_valid(self, is_superuser=False):
        # Make sure it's saved
        query = self.model.objects.filter(username=self.username)
        self.assertEqual(1, query.count())
        user = query[0]

        # Attributes
        self.assertEqual(user.get_username(), self.username)
        self.assertEqual(user.email, self.email)
        self.assertEqual(user.is_superuser, is_superuser)
        self.assertEqual(user.first_name, self.first_name)
        self.assertEqual(user.last_name, self.last_name)

        # check_password and has_usable_password should work
        self.assertFalse(get_user_model().has_usable_password(user))
        self.assertTrue(user.has_usable_password())
        self.assertTrue(user.check_password(self.password))
        user.set_unusable_password()
        self.assertFalse(user.has_usable_password())

        # Verify LDAP utilities
        self.assertTrue(username_exists(self.username))
        self.assertTrue(delete_user(self.username))

    def test_rename_user_with_save(self):
        """Renaming an LDAP user's username also renames the LDAP entry."""
        new_username = self.username + 'r2'
        self.assertIsNotNone(self.model.objects.create_user(
            username=self.username,
            email=self.email,
            password=self.password,
            first_name=self.first_name,
            last_name=self.last_name))
        user = self.model.objects.get(username=self.username)
        self.assertTrue(username_exists(self.username))
        self.assertFalse(username_exists(new_username))
        # Rename
        user.username = new_username
        user.save()
        self.assertRaises(
            self.model.DoesNotExist,
            self.model.objects.get,
            username=self.username)
        self.assertFalse(username_exists(self.username))
        self.assertTrue(username_exists(new_username))
        # Cleanup
        user.delete()
        self.assertFalse(username_exists(new_username))

    def test_invalid_rename_user_with_save(self):
        """Renaming to invalid username raises ValidationError."""
        new_username = '123_%s_rename_bad' % self.username
        self.assertIsNotNone(self.model.objects.create_user(
            username=self.username,
            email=self.email,
            password=self.password,
            first_name=self.first_name,
            last_name=self.last_name))
        user = self.model.objects.get(username=self.username)
        self.assertTrue(username_exists(self.username))
        self.assertFalse(username_exists(new_username))
        # Rename
        user.username = new_username
        self.assertRaises(ValidationError, user.save)
        # Nothing changed
        self.assertRaises(
            self.model.DoesNotExist,
            self.model.objects.get,
            username=new_username)
        self.assertTrue(username_exists(self.username))
        self.assertFalse(username_exists(new_username))
        # Cleanup
        user.username = self.username
        user.delete()
        self.assertFalse(username_exists(self.username))

    def test_save_update_email(self):
        """Updating email also edits LDAP entry's email attribute."""
        new_email = 'new' + self.email
        self.assertIsNotNone(self.model.objects.create_user(
            username=self.username,
            email=self.email,
            password=self.password,
            first_name=self.first_name,
            last_name=self.last_name))
        user = self.model.objects.get(username=self.username)
        self.assertEqual(self.email, get_email(self.username))
        # Rename
        user.email = new_email
        user.save()
        self.assertEqual(new_email, get_email(self.username))
        # Cleanup
        user.delete()
        self.assertFalse(username_exists(self.username))

    def test_delete_user(self):
        """Deleting user also deletes ldap entry."""
        self.assertIsNotNone(self.model.objects.create_user(
            username=self.username,
            email=self.email,
            password=self.password,
            first_name=self.first_name,
            last_name=self.last_name))
        user = self.model.objects.get(username=self.username)
        self.assertTrue(username_exists(self.username))
        user.delete()
        self.assertFalse(username_exists(self.username))


@override_settings(AUTH_USER_MODEL='auth.User')
class MakeLDAPUserTest(TestCase):
    def setUp(self):
        self.username = 'testuser'
        self.user = get_user_model().objects.create_user(
            username=self.username,
            email='test@tbp.berkeley.edu',
            password='password',
            first_name='John',
            last_name='Doe')

    def test_get_ldap_user_class(self):
        """Check that get_ldap_user returns an LDAPUser instance of the given
        user, without modifying the original object.
        """
        self.assertNotIsInstance(self.user, LDAPUser)
        make_ldap_user(self.user)
        self.assertIsInstance(self.user, LDAPUser)
        self.assertEqual(self.user.get_username(), self.username)

    def test_num_sql_queries(self):
        """Ensure that the method leads to no additional SQL queries changing
        the user to an instance of LDAPUser.
        """
        # pylint: disable=E1103
        with self.assertNumQueries(0):
            make_ldap_user(self.user)
            self.assertIsInstance(self.user, LDAPUser)
            self.assertEqual(self.user.get_username(), self.username)


class AuthenticationFormTest(TestCase):
    fixtures = ['groups.yaml']

    def setUp(self):
        self.username = 'testuser'
        self.password = 'password'
        self.user = get_user_model().objects.create_user(
            username=self.username,
            email='test@tbp.berkeley.edu',
            password=self.password,
            first_name='John',
            last_name='Doe')
        self.form_data = {
            'username': self.username,
            'password': self.password
        }

    def test_regular_user_auth_succeeds(self):
        """Test whether a non-company user can log in as expected."""
        form = AuthenticationForm(None, self.form_data)
        self.assertTrue(form.is_valid())

    def test_company_user_auth_succeeds_for_valid_account(self):
        """Verify that a company rep user can log in if their company's
        subscription is not expired.
        """
        # Create a company rep for the user, with a company that is active
        # (is_expired returns False)
        company = Company(name='Test Company',
                          expiration_date=datetime.date.today())
        company.save()
        with patch.object(Company, 'is_expired',
                          return_value=False) as mock_is_expired:
            rep = CompanyRep(user=self.user, company=company)
            rep.save()

            # Ensure that the user can be authenticated
            form = AuthenticationForm(None, self.form_data)
            self.assertTrue(form.is_valid())
        self.assertEquals(mock_is_expired.call_count, 1)

    def test_company_user_auth_fails_for_expired_account(self):
        """Verify that a company rep user cannot log in if their company's
        subscription is expired.
        """
        # Create a company rep for the user, with a company that has an expired
        # subscription (is_expired returns True)
        company = Company(name='Test Company',
                          expiration_date=datetime.date.today())
        company.save()
        with patch.object(Company, 'is_expired',
                          return_value=True) as mock_is_expired:
            rep = CompanyRep(user=self.user, company=company)
            rep.save()

            # Ensure that the user cannot be authenticated
            form = AuthenticationForm(None, self.form_data)
            self.assertFalse(form.is_valid())
            expected_error_msg = (
                '{}\'s subscription to this website has expired'.format(
                    company.name))
            self.assertIn(expected_error_msg, form.non_field_errors()[0])
        self.assertEquals(mock_is_expired.call_count, 1)
