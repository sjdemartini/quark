from chosen import forms

from quark.accounts.models import QuarkUser
from quark.accounts.models import LDAPQuarkUser


def user_common_name_label(obj):
    """Returns common name label for a given object."""
    if isinstance(obj, QuarkUser) or isinstance(obj, LDAPQuarkUser):
        return obj.get_common_name()
    try:
        return obj.get_full_name()  # A default User model method
    except AttributeError:  # If no get_full_name method available
        return str(obj)


class UserCommonNameChoiceField(forms.ChosenModelChoiceField):
    """A ModelChoiceField that makes labels use users' common names.

    The choice field makes the labels for the choices appear as Users'
    common names rather than simply using the unicode display for User, which
    is the default label.

    Note that this field inherits from ChosenModelChoiceField in order to
    make use of the Chosen widget for display (allowing for searching in the
    HTML select box), for additional convenience.
    """
    def label_from_instance(self, obj):
        return user_common_name_label(obj)


class UserCommonNameMultipleChoiceField(forms.ChosenModelMultipleChoiceField):
    """A ModelMultipleChoiceField that makes labels use users' common names.

    See an explanation of this field's utility in UserCommonNameChoiceField
    above, since the basic structure is the same.
    """
    def label_from_instance(self, obj):
        return user_common_name_label(obj)
