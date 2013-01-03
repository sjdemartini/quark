import mox

from django import forms
from django.core import mail
from django.test import TestCase
from django.test.client import Client
from django.test.utils import override_settings
from django.utils import unittest

from quark.auth.models import User
from quark.emailer.forms import ContactForm, ContactCaptcha
#from quark.events.models import Event


class ContactFormTest(unittest.TestCase):
    def test_custom_error_messages(self):
        form = ContactForm({'name': '', 'email': '', 'message': '',
                            'subject': '', 'author': ''})
        self.assertFalse(form.is_valid())

        name = form.errors.get('name', None)
        email = form.errors.get('email', None)
        message = form.errors.get('message', None)
        subject = form.errors.get('subject', None)
        author = form.errors.get('author', 'no error')

        self.assertEqual(len(name), 1)
        self.assertEqual(len(email), 1)
        self.assertEqual(len(message), 1)
        self.assertEqual(len(subject), 1)

        self.assertIn('Please provide your name.', name)
        self.assertIn('Please provide your email address.', email)
        self.assertIn('Please provide a message.', message)
        self.assertIn('Please provide a subject.', subject)

        self.assertEqual(author, 'no error')

    def test_message_too_short(self):
        form = ContactForm({'name': 'John Doe',
                            'email': 'test@tbp.berkeley.edu',
                            'message': 'Too short',
                            'subject': 'Error test',
                            'author': ''})
        self.assertFalse(form.is_valid())
        message = form.errors.get('message', None)
        self.assertEqual(len(message), 1)
        self.assertIn('Please enter a longer message.', message)

    def test_message_valid(self):
        form = ContactForm({'name': 'John Doe',
                            'email': 'test@tbp.berkeley.edu',
                            'message': 'Long enough' * 10,
                            'subject': 'Error test',
                            'author': ''})
        self.assertTrue(form.is_valid())
        message = form.errors.get('message', 'no error')
        self.assertEqual(message, 'no error')


@override_settings(HELPDESK_ADDRESS='test_hd@tbp.berkeley.edu')
class HelpdeskEmailerTest(TestCase):
    urls = 'quark.emailer.test_urls'

    def setUp(self):
        self.client = Client()
        self.mox = mox.Mox()
        self.default_entry = {'name': 'Test User',
                              'email': 'test@tbp.berkeley.edu',
                              'message': 'Message text' * 10,
                              'subject': 'Error test',
                              'author': '',
                              'recaptcha': 'whatever'}

        mock_fields = ContactCaptcha.base_fields.copy()
        self.mox.StubOutWithMock(ContactCaptcha, 'base_fields')
        mock_fields['recaptcha'] = forms.CharField(
            error_messages={'required': 'Please fill this in.'})
        ContactCaptcha.base_fields = mock_fields
        self.mox.ReplayAll()

    def tearDown(self):
        self.mox.VerifyAll()
        self.mox.UnsetStubs()
        self.mox.ResetAll()

    def test_get_request(self):
        response = self.client.get('/helpdesk/')
        # pylint: disable=E1103
        self.assertEqual(response.status_code, 302)

    def test_spam_check(self):
        submit_data = self.default_entry.copy()
        submit_data['author'] = 'Spambot'
        with self.settings(HELPDESK_SEND_SPAM=False):
            response = self.client.post('/helpdesk/', submit_data)
        context = response.context

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject[:15], '[Helpdesk spam]')

        self.assertEqual(context['result_message'], 'Successfully sent!')
        self.assertEqual(context['status'], 0)

    def test_invalid_entry(self):
        response = self.client.post('/helpdesk/', {'name': ''})

        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(response.context.get('status', False))
        self.assertFalse(response.context.get('result_message', False))

    def test_message_sent(self):
        with self.settings(HELPDESK_CC_ASKER=False, ENABLE_HELPDESKQ=False):
            response = self.client.post('/helpdesk/', self.default_entry)
        context = response.context

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['test_hd@tbp.berkeley.edu'])
        self.assertEqual(mail.outbox[0].from_email,
                         'Test User <test@tbp.berkeley.edu>')

        self.assertEqual(context['result_message'], 'Successfully sent!')
        self.assertEqual(context['status'], 0)

    def test_cc_sent(self):
        with self.settings(HELPDESK_CC_ASKER=True, ENABLE_HELPDESKQ=False):
            response = self.client.post('/helpdesk/', self.default_entry)
        context = response.context

        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].to,
                         ['Test User <test@tbp.berkeley.edu>'])
        self.assertEqual(mail.outbox[0].from_email,
                         'TBP Helpdesk <test_hd@tbp.berkeley.edu>')
        self.assertEqual(mail.outbox[1].to, ['test_hd@tbp.berkeley.edu'])
        self.assertEqual(mail.outbox[1].from_email,
                         'Test User <test@tbp.berkeley.edu>')

        self.assertEqual(context['result_message'], 'Successfully sent!')
        self.assertEqual(context['status'], 0)

    def test_assignment_sent(self):
        with self.settings(ENABLE_HELPDESKQ=True, HELPDESK_CC_ASKER=False):
            response = self.client.post('/helpdesk/', self.default_entry)
        context = response.context

        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].to, ['test_hd@tbp.berkeley.edu'])
        self.assertEqual(mail.outbox[0].from_email,
                         'Test User <test@tbp.berkeley.edu>')
        self.assertEqual(mail.outbox[1].from_email,
                         'helpdeskq@tbp.berkeley.edu')

        self.assertEqual(context['result_message'], 'Successfully sent!')
        self.assertEqual(context['status'], 0)

    # TODO(nitishp) Do after removing pickling in helpdesk models
    def test_saved_messages(self):
        pass


class EventEmailerTest(TestCase):
    urls = 'quark.emailer.test_urls'

    def setUp(self):
        self.client = Client()
        # TODO(nitishp) make an officer after permissions decorators are done
        self.user = User.objects.create_user(username='testuser',
                                             email='test@tbp.berkeley.edu',
                                             password='secretpass',
                                             first_name='Test',
                                             last_name='User')
        self.client.login(username='testuser', password='secretpass')
        # TODO(nitishp) finish checking events when EventSignUp is ported
        # self.event = Event()

    def test_not_logged_in(self):
        self.client.logout()
        req_get = self.client.get('/event/')
        req_post = self.client.post('/event/', {
            'name': 'Test User',
            'email': 'test@tbp.berkeley.edu',
            'message': 'Message text' * 10,
            'subject': 'Error test',
            'author': ''})
        # pylint: disable=E1103
        self.assertEqual(req_post.status_code, 302)
        # pylint: disable=E1103
        self.assertEqual(req_get.status_code, 302)

    # TODO(nitishp) needs EventSignUp model to function
    def test_new_form(self):
        pass
    #    response = self.client.get('/event/')
    #    self.assertEqual(response.status_code, 200)

    def test_message_sent(self):
        pass

    def test_no_recipients(self):
        pass
