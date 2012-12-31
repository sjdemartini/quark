from django.contrib.auth.models import User as DefaultUser
from django.test import TestCase
from django.test.utils import override_settings

from quark.auth.models import get_user_model
from quark.auth.models import LDAPQuarkUser
from quark.auth.models import QuarkUser
from quark.qldap.utils import username_exists
from quark.qldap.utils import delete_user


class UserModelTest(TestCase):
    @override_settings(AUTH_USER_MODEL='auth.User')
    def get_correct_user_model(self):
        self.assertEqual(get_user_model(), DefaultUser)

    @override_settings(AUTH_USER_MODEL='nonexistent.User')
    def get_wrong_user_model(self):
        self.assertRaises(NameError, get_user_model)


@override_settings(AUTH_USER_MODEL='auth.QuarkUser')
class CreateQuarkUserTestCase(TestCase):
    def setUp(self):
        self.model = QuarkUser
        self.username = 'testuser'
        self.email = 'test@tbp.berkeley.edu'
        self.password = 'testpassword'
        self.first_name = 'Mike'
        self.last_name = 'McTest'

    def test_correct_user_model(self):
        """Make sure this test is using the proper model"""
        self.assertEqual(self.model, QuarkUser)

    def test_create_user(self):
        """Tests create_user"""
        self.assertFalse(
            self.model.objects.filter(username=self.username).exists())
        self.assertIsNotNone(self.model.objects.create_user(
            username=self.username,
            email=self.email,
            password=self.password,
            first_name=self.first_name,
            last_name=self.last_name))
        # Make sure it's saved
        query = self.model.objects.filter(username=self.username)
        self.assertEqual(1, query.count())
        user = query[0]
        # Attributes
        self.assertEqual(user.username, self.username)
        self.assertEqual(user.email, self.email)
        self.assertEqual(user.first_name, self.first_name)
        self.assertEqual(user.last_name, self.last_name)
        self.assertEqual(user.preferred_name, self.first_name)
        self.assertEqual(user.middle_name, '')
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password(self.password))
        # Name methods
        full_name = '%s %s' % (self.first_name, self.last_name)
        self.assertEqual(user.get_full_name(), full_name)
        self.assertEqual(user.get_common_name(), full_name)
        self.assertEqual(user.get_short_name(), self.first_name)


@override_settings(AUTH_USER_MODEL='auth.LDAPQuarkUser')
class CreateLDAPQuarkUserTestCase(CreateQuarkUserTestCase):
    def setUp(self):
        super(CreateLDAPQuarkUserTestCase, self).setUp()
        self.model = LDAPQuarkUser

    def tearDown(self):
        if username_exists(self.username):
            self.assertTrue(delete_user(self.username))

    def test_correct_user_model(self):
        """Make sure this test is using the proper model"""
        self.assertEqual(self.model, LDAPQuarkUser)

    def test_create_user(self):
        if username_exists(self.username):
            self.assertTrue(delete_user(self.username))
        super(CreateLDAPQuarkUserTestCase, self).test_create_user()
        self.assertTrue(username_exists(self.username))
        self.assertTrue(delete_user(self.username))

    def test_bad_create_user(self):
        """
        Creating an LDAP user directly via model instantiation should not
        actually save the new user into the database
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
        user.save()

        query = self.model.objects.filter(username=bad_username)
        self.assertEqual(0, query.count())
        self.assertFalse(username_exists(bad_username))

    def test_delete_user(self):
        """Deleting user also deletes ldap entry"""
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
