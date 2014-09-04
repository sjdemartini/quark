import re

from django import forms
from django.core.mail import BadHeaderError
from django.core.mail import EmailMessage

from quark.emailer.fields import ReCaptchaField


class ContactForm(forms.Form):
    """
    A generic form that allows users to contact other people. It's used for
    both Helpdesk and the Events emailer.
    """
    MIN_MESSAGE_LENGTH = 10
    name = forms.CharField(
        error_messages={'required': 'Please provide your name.'})
    email = forms.EmailField(
        error_messages={'required': 'Please provide your email address.'})
    subject = forms.CharField(
        error_messages={'required': 'Please provide a subject.'})
    message = forms.CharField(widget=forms.Textarea,
                              error_messages={
                                  'required': 'Please provide a message.'})

    # anti-spam field; matches wordpress
    author = forms.CharField(widget=forms.HiddenInput, required=False)

    def clean_message(self):
        message = self.cleaned_data.get('message', '')

        if len(message) <= ContactForm.MIN_MESSAGE_LENGTH:
            raise forms.ValidationError('Please enter a longer message.')

        # Always return the cleaned data.
        return message

    def clean_name(self):
        name = self.cleaned_data.get('name', '')

        # check for invalid characters; 201C, 201D are open/close double quotes
        if re.search(ur'["<>@,.\u201C\u201D]', name):
            raise forms.ValidationError('Your name can\'t contain the '
                                        'characters <, >, @, comma, ., or ".')

        return name

    def send_email(self, to_email=None, cc_list=None, bcc_list=None,
                   headers=None, name='', email='', from_email='',
                   subject='', message=''):
        # returns a status True for success and False for failure
        if not (to_email or cc_list or bcc_list):
            raise BadHeaderError('No recipients found.')

        name = name or self.cleaned_data['name']
        email = email or self.cleaned_data['email']
        from_email = from_email or '"{}" <{}>'.format(name, email)
        subject = subject or self.cleaned_data['subject']
        body = message or self.cleaned_data['message']
        to_email = to_email or []
        cc_list = cc_list or []
        bcc_list = bcc_list or []
        headers = headers or {}

        sent_message = EmailMessage(to=to_email,
                                    cc=cc_list,
                                    bcc=bcc_list,
                                    headers=headers,
                                    subject=subject,
                                    body=body,
                                    from_email=from_email)
        try:
            sent_message.send()
            return True
        except:
            return False


class EventContactForm(ContactForm):
    """Use ContactForm but do not allow editing of sender's name and email.  """
    def __init__(self, *args, **kwargs):
        super(EventContactForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget = forms.HiddenInput()
        self.fields['email'].widget = forms.HiddenInput()


class ContactCaptcha(ContactForm):
    """
    Taken from: http://www.djangosnippets.org/snippets/1653/

    This is an extension of the ContactForm that also includes a ReCaptcha.
    This is used for Helpdesk to prevent spam. It's more effective than the
    author field.
    """
    recaptcha = ReCaptchaField(
        label='CAPTCHA', error_messages={
            'required': 'Please fill this in.',
            'captcha_invalid': 'Come on, we know you can read.'})
