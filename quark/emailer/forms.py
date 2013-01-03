from django import forms

from quark.emailer.fields import ReCaptchaField


class ContactForm(forms.Form):
    """
    A generic form that allows users to contact other people. It's used for
    both Helpdesk and the Events emailer.
    """
    name = forms.CharField(
        error_messages={'required': 'Please provide your name.'})
    email = forms.EmailField(
        error_messages={'required': 'Please provide your email address.'})
    message = forms.CharField(widget=forms.Textarea,
                              error_messages={
                                  'required': 'Please provide a message.'})
    subject = forms.CharField(
        error_messages={'required': 'Please provide a subject.'})

    # anti-spam field; matches wordpress
    author = forms.CharField(widget=forms.HiddenInput, required=False)

    def clean_message(self):
        message = self.cleaned_data.get("message", '')

        if len(message) <= 30:
            raise forms.ValidationError('Please enter a longer message.')

        # Always return the cleaned data.
        return message


class ContactCaptcha(ContactForm):
    """
    Taken from: http://www.djangosnippets.org/snippets/1653/

    This is an extension of the ContactForm that also includes a ReCaptcha.
    This is used for Helpdesk to prevent spam. It's more effective than the
    author field.
    """
    recaptcha = ReCaptchaField(
        error_messages={
            'required': 'Please fill this in.',
            'captcha_invalid': 'Come on, we know you can read.'})
