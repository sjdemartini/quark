from chosen import forms as chosen_forms
from django import forms
from django.conf import settings
from django.forms.extras import SelectDateWidget
from django.utils import timezone

from quark.qldap.utils import set_email
from quark.user_profiles.models import UserProfile


class UserProfileForm(forms.ModelForm):
    # Include the user's username, first name, last name, and email address
    # from the user model, but don't allow the user to edit any except the
    # email address
    username = forms.CharField(required=False)
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    email = forms.EmailField(label='Primary email address')
    gender = forms.ChoiceField(choices=UserProfile.GENDER_CHOICES,
                               widget=forms.RadioSelect,
                               required=True)

    class Meta(object):
        model = UserProfile
        fields = ('username', 'first_name', 'preferred_name', 'middle_name',
                  'last_name', 'birthday', 'gender', 'email', 'alt_email',
                  'cell_phone', 'receive_text', 'home_phone', 'local_address1',
                  'local_address2', 'local_city', 'local_state', 'local_zip',
                  'perm_address1', 'perm_address2', 'perm_city', 'perm_state',
                  'perm_zip', 'international_address')
        widgets = {
            'local_state': chosen_forms.ChosenSelect,
            'perm_state': chosen_forms.ChosenSelect
        }

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        # Set the initial values for the user model fields based on those
        # corresponding values. Note that editing a user profile only makes
        # sense if an instance is provided, as every user will have a user
        # profile.
        self.fields['username'].initial = self.instance.user.username
        self.fields['first_name'].initial = self.instance.user.first_name
        self.fields['last_name'].initial = self.instance.user.last_name
        self.fields['email'].initial = self.instance.user.email

        # Disable editing for user account fields (besides email):
        self.fields['username'].widget.attrs['disabled'] = 'disabled'
        self.fields['first_name'].widget.attrs['disabled'] = 'disabled'
        self.fields['last_name'].widget.attrs['disabled'] = 'disabled'

        # TODO(sjdemartini): Add clarifying help_text regarding forwarding email
        # to the "email" field here, as it will affect the forwarding email
        # address once LDAP modification is enabled in the save() method.

        # Change the range of dates shown for the birthday field to only
        # relevant times
        year_max = timezone.now().year - 10
        year_min = year_max - 70
        self.fields['birthday'].widget = SelectDateWidget(
            years=range(year_min, year_max))

        # Make the local address required for someone editing their user
        # profile:
        self.fields['local_address1'].required = True
        self.fields['local_city'].required = True
        self.fields['local_state'].required = True
        self.fields['local_zip'].required = True

    def clean(self):
        """Require that the profile has either a permanent or international
        address.
        """
        cleaned_data = super(UserProfileForm, self).clean()
        international_address = cleaned_data.get('international_address')
        perm_address1 = cleaned_data.get('perm_address1')
        perm_city = cleaned_data.get('perm_city')
        perm_state = cleaned_data.get('perm_state')
        perm_zip = cleaned_data.get('perm_zip')
        if (not international_address) and not (
                perm_address1 and perm_city and perm_state and perm_zip):
            raise forms.ValidationError(
                'A permanent or international address is required.')
        return cleaned_data

    def save(self, *args, **kwargs):
        """Save the user email if it has changed."""
        email = self.cleaned_data['email']

        if self.instance.user.email != email:
            self.instance.user.email = email
            self.instance.user.save(update_fields=['email'])
            # Save email address to LDAP if LDAP is enabled
            if getattr(settings, 'USE_LDAP', False):
                set_email(self.instance.user.get_username(), email)

        return super(UserProfileForm, self).save(*args, **kwargs)


class UserProfilePictureForm(forms.ModelForm):
    class Meta(object):
        model = UserProfile
        fields = ('picture',)
        labels = {
            'picture': 'Upload a new picture'
        }
        widgets = {
            'picture': forms.ClearableFileInput(attrs={'accept': 'image/*'})
        }
