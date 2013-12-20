from chosen import forms
from django.contrib.auth import get_user_model

from quark.user_profiles.models import UserProfile


user_model = get_user_model()


class UserCommonNameFieldMixin(object):
    """A mixin for using users' common names in a form field.

    The choice field makes the labels for the choices appear as Users'
    common names rather than simply using the unicode display for User, which
    is the default label.

    The default queryset (if none is provided) is all users.
    """
    def __init__(self, queryset=user_model.objects.all(), *args, **kwargs):
        super(UserCommonNameFieldMixin, self).__init__(
            *args, queryset=queryset, **kwargs)
        # Ensure that user profiles are fetched along with all users in the
        # queryset, since user profiles are used to get the label
        self.queryset = self.queryset.select_related('userprofile')

    def label_from_instance(self, obj):
        """Return the common name label for a given object."""
        try:
            # Try getting the UserProfile as a reverse one-to-one relation, and
            # call its get_common_name method if available
            return obj.userprofile.get_common_name()
        except UserProfile.DoesNotExist:
            pass

        try:
            return obj.get_full_name()  # A default User model method
        except AttributeError:  # If no get_full_name method available
            return str(obj)


class UserCommonNameChoiceField(UserCommonNameFieldMixin,
                                forms.ChosenModelChoiceField):
    """A ModelChoiceField that makes labels use users' common names.

    Note that this field inherits from ChosenModelChoiceField in order to make
    use of the Chosen widget for display (allowing for searching in the HTML
    select box), for additional convenience.
    """
    pass


class UserCommonNameMultipleChoiceField(UserCommonNameFieldMixin,
                                        forms.ChosenModelMultipleChoiceField):
    """A ModelMultipleChoiceField that makes labels use users' common names.

    See an explanation of this field's utility in UserCommonNameChoiceField
    above, since the basic structure is the same.
    """
    pass
