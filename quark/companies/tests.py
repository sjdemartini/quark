import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase
from freezegun import freeze_time

from quark.companies.forms import CompanyRepCreationForm
from quark.companies.models import Company
from quark.companies.models import CompanyRep


class CompanyTest(TestCase):
    fixtures = ['groups.yaml']

    @freeze_time('2015-03-14')
    def test_company_is_expired(self):
        """Make sure is_expired properly indicates expiration."""
        today = datetime.date.today()

        # Make the company's expiration in the past:
        expiration = today - datetime.timedelta(days=1)
        company = Company(name='Test Company', expiration_date=expiration)
        company.save()
        self.assertTrue(company.is_expired())

    @freeze_time('2015-03-14')
    def test_company_is_not_expired(self):
        """Make sure is_expired properly indicates non-expiration."""
        today = datetime.date.today()

        # Make the company's expiration date weeks in the future:
        expiration = today + datetime.timedelta(weeks=5)
        company = Company(name='Test Company', expiration_date=expiration)
        company.save()
        self.assertFalse(company.is_expired())

        # Move the expiration date to today, which should be the final
        # non-expired day:
        expiration = today
        company.expiration_date = expiration
        company.save()
        self.assertFalse(company.is_expired())


class CompanyFormsTest(TestCase):
    fixtures = ['groups.yaml']

    def setUp(self):
        expiration = datetime.date.today() + datetime.timedelta(weeks=5)
        self.company = Company(name='Test Company', expiration_date=expiration)
        self.company.save()

        self.user_model = get_user_model()

    def test_company_rep_creation_form(self):
        """Ensure that the company rep creation form works to create a new user
        and the corresponding CompanyRep object.
        """
        # The email addresses don't match
        rep_attrs = {
            'username': 'repuser',
            'email': 'testrep@example.com',
            'confirm_email': 'testrep@example.comm',
            'first_name': 'Jane',
            'last_name': 'Doe',
            'company': self.company.pk
        }
        form = CompanyRepCreationForm(rep_attrs)
        self.assertFalse(form.is_valid())

        # Fix the email address mismatch
        rep_attrs['confirm_email'] = 'testrep@example.com'
        form = CompanyRepCreationForm(rep_attrs)
        self.assertTrue(form.is_valid())
        form.save()

        # Check that a user was created with the appropriate attributes and
        # an unusable password:
        rep_user = self.user_model.objects.get(username=rep_attrs['username'])
        self.assertEquals(rep_user.get_username(), rep_attrs['username'])
        self.assertEquals(rep_user.email, rep_attrs['email'])
        self.assertEquals(rep_user.first_name, rep_attrs['first_name'])
        self.assertEquals(rep_user.last_name, rep_attrs['last_name'])
        self.assertEquals(rep_user.last_name, rep_attrs['last_name'])
        self.assertFalse(rep_user.has_usable_password())

        # Check that the CompanyRep was created correctly:
        rep = rep_user.companyrep
        self.assertEquals(rep.company, self.company)


class CompanyRepViewTest(TestCase):
    """Test the CompanyRep views."""

    fixtures = ['groups.yaml']

    def setUp(self):
        expiration = datetime.date.today() + datetime.timedelta(weeks=5)
        self.company = Company(name='Test Company', expiration_date=expiration)
        self.company.save()

        self.user_model = get_user_model()

        # Create a user who has permissions for companies and company reps
        self.user = self.user_model.objects.create_user(
            username='testuser',
            email='it@tbp.berkeley.edu',
            password='password',
            first_name='John',
            last_name='Superuser')

        company_content_type = ContentType.objects.get_for_model(Company)
        rep_content_type = ContentType.objects.get_for_model(CompanyRep)
        company_add_permission = Permission.objects.get(
            content_type=company_content_type, codename='add_company')
        company_change_permission = Permission.objects.get(
            content_type=company_content_type, codename='change_company')
        companies_view_permission = Permission.objects.get(
            content_type=company_content_type, codename='view_companies')
        rep_add_permission = Permission.objects.get(
            content_type=rep_content_type, codename='add_companyrep')
        rep_change_permission = Permission.objects.get(
            content_type=rep_content_type, codename='change_companyrep')
        rep_delete_permission = Permission.objects.get(
            content_type=rep_content_type, codename='delete_companyrep')
        self.user.user_permissions.add(
            company_add_permission, company_change_permission,
            companies_view_permission, rep_add_permission,
            rep_change_permission, rep_delete_permission)

    def test_company_rep_create_view(self):
        """Ensure that the user can create a company rep successfully, and that
        the company rep receives a password reset email.
        """
        self.assertTrue(self.client.login(
            username=self.user.username, password='password'))
        create_rep_url = reverse('companies:rep-create')
        rep_data = {
            'username': 'testrepuser',
            'email': 'testrep@example.com',
            'confirm_email': 'testrep@example.com',
            'first_name': 'Jane',
            'last_name': 'Doe',
            'company': self.company.pk
        }
        # Make sure there are currently no company reps and that no emails have
        # been sent
        self.assertFalse(CompanyRep.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

        # Create the rep using the view
        response = self.client.post(create_rep_url, rep_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, 'Successfully created a new company rep account')
        self.assertContains(response, rep_data['username'])
        self.assertContains(response, self.company.name)

        # Check that the rep account was successfully created
        rep_user = self.user_model.objects.get(username=rep_data['username'])
        self.assertEquals(rep_user.companyrep, CompanyRep.objects.get())
        self.assertEquals(rep_user.companyrep.company, self.company)

        # Check the sent email to ensure the company rep received an email for
        # setting their password
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, [rep_user.email])

        # Make sure the email contains a password reset link:
        self.assertIn('accounts/password/reset', email.body)

    def test_companyrep_delete_view(self):
        """Ensure that representatives can be deleted and that deleted reps
        have their accounts disabled.
        """
        company = Company(expiration_date='3000-01-01')
        company.save()
        companyrep_user = self.user_model.objects.create_user(
            username='test_rep',
            password='password')
        companyrep_user_pk = companyrep_user.pk
        companyrep = CompanyRep(company=company, user=companyrep_user)
        companyrep.save()

        self.assertTrue(self.client.login(
            username=self.user.username, password='password'))
        self.assertTrue(companyrep_user.is_active)
        self.assertTrue(self.client.login(username='test_rep',
                                          password='password'))

        # Use the view
        self.assertTrue(self.client.login(
            username=self.user.username, password='password'))
        response = self.client.get(
            reverse('companies:rep-delete', args=(companyrep.pk,)),
            follow=True)
        self.assertContains(response, 'Are you sure')
        self.client.post(
            reverse('companies:rep-delete', args=(companyrep.pk,)),
            follow=True)

        # Check that everything has been deleted
        self.assertFalse(CompanyRep.objects.exists())

        # Check that the rep can't log in
        companyrep_user = User.objects.get(pk=companyrep_user_pk)
        self.assertFalse(companyrep_user.is_active)
        self.assertFalse(self.client.login(
            username='test_rep', password='password'))
