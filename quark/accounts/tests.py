import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as DefaultUser
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.test.utils import override_settings

from quark.accounts.models import make_ldap_user
from quark.accounts.models import LDAPUser
from quark.qldap.utils import username_exists
from quark.qldap.utils import delete_user


class UserModelTest(TestCase):
    @override_settings(AUTH_USER_MODEL='auth.User')
    def get_correct_user_model(self):
        self.assertEqual(get_user_model(), DefaultUser)

    @override_settings(AUTH_USER_MODEL='nonexistent.User')
    def get_wrong_user_model(self):
        self.assertRaises(NameError, get_user_model)


@override_settings(AUTH_USER_MODEL='accounts.LDAPUser')
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

        # check_password should work, but the Django user password should be
        # unusable, since password only stored in LDAP
        self.assertTrue(user.check_password(self.password))
        self.assertFalse(user.has_usable_password())

        # Verify LDAP utilities
        self.assertTrue(username_exists(self.username))
        self.assertTrue(delete_user(self.username))

    def test_bad_create_user(self):
        """Creating an LDAP user directly via model instantiation should not
        actually save the new user into the database and should raise an error.
        """
        bad_username = 'baduser'
        if username_exists(bad_username):
            self.assertTrue(delete_user(bad_username))
        user = self.model(
            username=bad_username,
            email=self.email,
            password=self.password,
            first_name=self.first_name,
            last_name=self.last_name)
        self.assertRaises(ValidationError, user.save)

        query = self.model.objects.filter(username=bad_username)
        self.assertEqual(0, query.count())
        self.assertFalse(username_exists(bad_username))

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
        self.username = 'bentleythebent'
        self.user = get_user_model().objects.create_user(
            username=self.username,
            email='it@tbp.berkeley.edu',
            password='testofficerpw',
            first_name='Bentley',
            last_name='Bent')

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
