from chosen import forms as chosen_forms
from django import forms
from django.conf import settings
from django.forms.extras import SelectDateWidget
from django.utils import timezone

from quark.base.models import Major
from quark.base.models import Term
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
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea,
        help_text='Bio is optional for candidates'
    )
    major = chosen_forms.ChosenModelMultipleChoiceField(Major.objects)
    start_term = forms.ModelChoiceField(Term.objects.get_terms(
        reverse=True).exclude(id=Term.objects.get_current_term().id))
    grad_term = forms.ModelChoiceField(Term.objects.get_terms(
        include_future=True))

    class Meta(object):
        model = UserProfile
        fields = ('username', 'first_name', 'preferred_name', 'middle_name',
                  'last_name', 'birthday', 'gender', 'email', 'alt_email',
                  'major', 'start_term', 'grad_term', 'bio', 'cell_phone',
                  'receive_text', 'home_phone', 'local_address1',
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
        student_org_user_profile = self.instance.get_student_org_user_profile()
        if student_org_user_profile:
            self.fields['bio'].initial = student_org_user_profile.bio

        # Set initial values for college student info
        college_student_info = self.instance.get_college_student_info()
        if college_student_info:
            self.fields['major'].initial = college_student_info.major.all()
            self.fields['start_term'].initial = \
                college_student_info.start_term
            self.fields['grad_term'].initial = college_student_info.grad_term

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
        cleaned_data = super(UserProfileForm, self).clean()
        UserProfileForm.clean_userprofile_addresses(cleaned_data)
        return cleaned_data

    @staticmethod
    def clean_userprofile_addresses(cleaned_data):
        """Require that the submitted form has either a permanent or
        international address."""
        international_address = cleaned_data.get('international_address')
        perm_address1 = cleaned_data.get('perm_address1')
        perm_city = cleaned_data.get('perm_city')
        perm_state = cleaned_data.get('perm_state')
        perm_zip = cleaned_data.get('perm_zip')
        if (not international_address) and not (
                perm_address1 and perm_city and perm_state and perm_zip):
            raise forms.ValidationError(
                'A permanent or international address is required.')

    def save(self, *args, **kwargs):
        """Save the user email if it has changed."""
        email = self.cleaned_data['email']

        if self.instance.user.email != email:
            self.instance.user.email = email
            self.instance.user.save(update_fields=['email'])
            # Save email address to LDAP if LDAP is enabled
            if getattr(settings, 'USE_LDAP', False):
                set_email(self.instance.user.get_username(), email)

        bio = self.cleaned_data['bio']
        student_org_user_profile = self.instance.get_student_org_user_profile()
        if student_org_user_profile and student_org_user_profile.bio != bio:
            student_org_user_profile.bio = bio
            student_org_user_profile.save(update_fields=['bio'])

        major = self.cleaned_data['major']
        start_term = self.cleaned_data['start_term']
        grad_term = self.cleaned_data['grad_term']
        college_student_info = self.instance.get_college_student_info()
        if college_student_info:
            update_fields = []
            if college_student_info.major != major:
                college_student_info.major = major
            if college_student_info.start_term != start_term:
                college_student_info.start_term = start_term
                update_fields.append('start_term')
            if college_student_info.grad_term != grad_term:
                college_student_info.grad_term = grad_term
                update_fields.append('grad_term')
            college_student_info.save(update_fields=update_fields)

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
