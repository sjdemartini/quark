import os

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.models import User as DefaultUser
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
from mock import Mock

from quark.accounts.decorators import candidate_required
from quark.accounts.decorators import current_officer_required
from quark.accounts.decorators import officer_required
from quark.accounts.decorators import officer_types_required
from quark.accounts.models import CompanyQuarkUser
from quark.accounts.models import LDAPQuarkUser
from quark.accounts.models import QuarkUser
from quark.base.models import Term
from quark.base_tbp.models import Officer
from quark.base_tbp.models import OfficerPosition
from quark.candidates.models import Candidate
from quark.qldap.utils import username_exists
from quark.qldap.utils import delete_user


class UserModelTest(TestCase):
    @override_settings(AUTH_USER_MODEL='auth.User')
    def get_correct_user_model(self):
        self.assertEqual(get_user_model(), DefaultUser)

    @override_settings(AUTH_USER_MODEL='nonexistent.User')
    def get_wrong_user_model(self):
        self.assertRaises(NameError, get_user_model)


@override_settings(AUTH_USER_MODEL='accounts.QuarkUser')
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


@override_settings(AUTH_USER_MODEL='accounts.LDAPQuarkUser')
class CreateLDAPQuarkUserTestCase(CreateQuarkUserTestCase):
    def setUp(self):
        super(CreateLDAPQuarkUserTestCase, self).setUp()
        self.model = LDAPQuarkUser
        # Use unique name for LDAP
        rnd = os.getpid()
        self.username = 'testuser%d' % rnd
        self.email = 'test%d@tbp.berkeley.edu' % rnd

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


@override_settings(AUTH_USER_MODEL='accounts.CompanyQuarkUser')
class CreateCompanyQuarkUserTestCase(TestCase):
    def setUp(self):
        self.model = CompanyQuarkUser
        self.username = 'testcompany'
        self.email = 'testcompany@tbp.berkeley.edu'
        self.password = 'testpassword'
        self.company_name = 'Industry Company Inc.'

    def test_correct_user_model(self):
        """Make sure this test is using the proper model"""
        self.assertEqual(self.model, CompanyQuarkUser)

    def test_create_user(self):
        """Tests create_user"""
        self.assertFalse(
            self.model.objects.filter(username=self.username).exists())
        self.assertIsNotNone(self.model.objects.create_user(
            username=self.username,
            email=self.email,
            password=self.password,
            company_name=self.company_name))
        # Make sure it's saved
        query = self.model.objects.filter(username=self.username)
        self.assertEqual(1, query.count())
        user = query[0]
        # Attributes
        self.assertEqual(user.username, self.username)
        self.assertEqual(user.email, self.email)
        self.assertEqual(user.company_name, self.company_name)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password(self.password))

    def test_name_methods(self):
        user = self.model.objects.create_user(
            username=self.username,
            email=self.email,
            password=self.password,
            company_name=self.company_name)

        # Name methods
        self.assertEqual(user.get_full_name(), self.company_name)
        self.assertEqual(unicode(user),
                         '{} ({})'.format(self.username, self.company_name))
        self.assertEqual(user.get_short_name(), self.company_name)


class DecoratorsTest(TestCase):
    old_term = None
    term = None
    old_position = None
    position = None
    it_chair = None
    vpres = None

    def setUp(self):
        response = Mock(status_code=200)
        self.view = Mock(return_value=response)

        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@tbp.berkeley.edu',
            password='secretpass',
            first_name='Test',
            last_name='User')
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        self.request.session = {}

    def add_officer_positions(self, current=True):
        self.old_term = Term(term=Term.SPRING, year=2012, current=False)
        self.old_term.save()
        self.term = Term(term=Term.FALL, year=2012, current=True)
        self.term.save()
        self.old_position = OfficerPosition(
            position_type=OfficerPosition.TBP_OFFICER,
            short_name='IT',
            long_name='Information Technology',
            rank=2,
            mailing_list='IT')
        self.old_position.save()
        self.it_chair = Officer(user=self.user, position=self.old_position,
                                term=self.old_term, is_chair=True)
        self.it_chair.save()
        if current:
            self.position = OfficerPosition(
                position_type=OfficerPosition.TBP_OFFICER,
                short_name='VP',
                long_name='Vice President',
                rank=2,
                mailing_list='VP')
            self.position.save()
            self.vpres = Officer(user=self.user, position=self.position,
                                 term=self.term, is_chair=False)
            self.vpres.save()

    def test_not_logged_in(self):  # sanity check
        decorated_view = login_required(self.view)
        self.request.user = AnonymousUser()
        response = decorated_view(self.request)

        self.assertFalse(self.view.called)
        self.assertEqual(response.status_code, 302)

    def test_logged_in(self):  # sanity check
        decorated_view = login_required(self.view)
        self.request.user = self.user
        response = decorated_view(self.request)

        self.assertTrue(self.view.called)
        self.assertEqual(response.status_code, 200)

    def test_not_officer(self):
        decorated_view = officer_required(self.view)
        self.request.user = self.user
        self.assertRaises(PermissionDenied, decorated_view, self.request)

    def test_officer(self):
        decorated_view = officer_required(self.view)
        self.add_officer_positions()
        self.request.user = self.user
        response = decorated_view(self.request)

        self.assertTrue(self.view.called)
        self.assertEqual(response.status_code, 200)

    def test_not_current_officer(self):
        decorated_view = current_officer_required(self.view)
        self.add_officer_positions(current=False)
        self.request.user = self.user
        self.assertRaises(PermissionDenied, decorated_view, self.request)

    def test_current_officer(self):
        decorated_view = current_officer_required(self.view)
        self.add_officer_positions()
        self.request.user = self.user
        response = decorated_view(self.request)

        self.assertTrue(self.view.called)
        self.assertEqual(response.status_code, 200)

    def test_not_has_officer_types(self):
        decorator = officer_types_required(['vp'])
        decorated_view = decorator(self.view)
        self.add_officer_positions(current=False)
        self.request.user = self.user
        self.assertRaises(PermissionDenied, decorated_view, self.request)

    def test_has_officer_types(self):
        decorator = officer_types_required(['it'])
        decorated_view = decorator(self.view)
        self.add_officer_positions(current=False)
        self.request.user = self.user
        response = decorated_view(self.request)

        self.assertTrue(self.view.called)
        self.assertEqual(response.status_code, 200)

    def test_not_has_current_officer_types(self):
        decorator = officer_types_required(['it'], current=True)
        decorated_view = decorator(self.view)
        self.add_officer_positions()
        self.request.user = self.user
        self.assertRaises(PermissionDenied, decorated_view, self.request)

    def test_has_current_officer_types(self):
        decorator = officer_types_required(['execs'], current=True)
        decorated_view = decorator(self.view)
        self.add_officer_positions()
        self.request.user = self.user
        response = decorated_view(self.request)

        self.assertTrue(self.view.called)
        self.assertEqual(response.status_code, 200)

    def test_exclude_officer_types(self):
        decorator = officer_types_required(['it'], exclude=True)
        decorated_view = decorator(self.view)
        self.add_officer_positions()
        self.request.user = self.user
        self.assertRaises(PermissionDenied, decorated_view, self.request)

    def test_exclude_current_officer_types(self):
        decorator = officer_types_required(['vp'], current=True, exclude=True)
        decorated_view = decorator(self.view)
        self.add_officer_positions()
        self.request.user = self.user
        self.assertRaises(PermissionDenied, decorated_view, self.request)

        decorator = officer_types_required(['it'], current=True, exclude=True)
        decorated_view = decorator(self.view)
        response = decorated_view(self.request)

        self.assertTrue(self.view.called)
        self.assertEqual(response.status_code, 200)

    def test_not_candidate(self):
        decorated_view = candidate_required(self.view)
        self.request.user = self.user
        self.assertRaises(PermissionDenied, decorated_view, self.request)

    def test_candidate(self):
        decorated_view = candidate_required(self.view)
        self.term = Term(term=Term.SPRING, year=2012, current=True)
        self.term.save()
        candidate = Candidate(user=self.user, term=self.term)
        candidate.save()
        self.request.user = self.user
        response = decorated_view(self.request)

        self.assertTrue(self.view.called)
        self.assertEqual(response.status_code, 200)
