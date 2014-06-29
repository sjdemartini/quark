from chosen import forms as chosen_forms
from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.forms.extras import SelectDateWidget

from quark.accounts.forms import UserCreationForm
from quark.companies.models import Company
from quark.companies.models import CompanyRep


class CompanyForm(forms.ModelForm):
    """A simple form for editing a Company.

    This form is probably best suited to be used by company representatives.
    """
    class Meta(object):
        model = Company
        fields = ('name', 'website', 'logo')


class CompanyFormWithExpiration(CompanyForm):
    """Form for editing or creating a Company, including the ability to set the
    expiration date of the company account.

    This form should be used by website administrators, rather than by company
    representatives.
    """
    class Meta(CompanyForm.Meta):
        fields = ('name', 'website', 'logo', 'expiration_date')
        widgets = {
            'expiration_date': SelectDateWidget()
        }


class CompanyRepCreationForm(UserCreationForm):
    """Form for creating a user account for a company representative.

    This form creates a user account and an associated CompanyRep object, tying
    the rep to a particular company.

    This form should be used by website administrators. Representatives should
    not create accounts for themselves.
    """
    company = chosen_forms.ChosenModelChoiceField(
        queryset=Company.objects.all())
    confirm_email = forms.EmailField(label='Confirm email', required=True)

    class Meta(UserCreationForm.Meta):
        fields = ('company', 'username', 'first_name', 'last_name', 'email',
                  'confirm_email')
        widgets = {
            'expiration_date': SelectDateWidget()
        }

    def __init__(self, *args, **kwargs):
        super(CompanyRepCreationForm, self).__init__(*args, **kwargs)
        self.fields['email'].help_text = (
            'Please ensure that this address is correct! After this form is '
            'submitted, the company representative will receive an email at '
            'this address, which will allow them to set their account password.'
        )

        # Take out the password fields from the superclass form, since we set
        # an unusable password for the user in the save method, due to the fact
        # that this form is for someone creating an account for another person.
        del self.fields['password1']
        del self.fields['password2']

    def clean(self):
        cleaned_data = super(CompanyRepCreationForm, self).clean()
        email = cleaned_data.get('email')
        confirm_email = cleaned_data.get('confirm_email')
        if email != confirm_email:
            raise ValidationError('Emails do not match.')
        return cleaned_data

    @transaction.atomic
    def save(self, *args, **kwargs):
        """Save a CompanyRep object along with the new user account."""
        # Set password1 in the cleanded_data to None so that the user is given
        # an unusable password in the superclass save() method
        self.cleaned_data['password1'] = None
        rep_user = super(CompanyRepCreationForm, self).save(*args, **kwargs)
        rep_company = self.cleaned_data['company']
        CompanyRep(user=rep_user, company=rep_company).save()
        return rep_user
