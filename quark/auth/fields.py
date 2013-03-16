from chosen import forms

from quark.auth.models import QuarkUser
from quark.auth.models import LDAPQuarkUser
from quark.auth.models import CompanyQuarkUser


def user_common_name_label(obj):
    if isinstance(obj, QuarkUser) or isinstance(obj, LDAPQuarkUser):
        return obj.get_common_name()
    if isinstance(obj, CompanyQuarkUser):
        return obj.get_full_name()
    return unicode(obj)


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
    above.
    """
    def label_from_instance(self, obj):
        return user_common_name_label(obj)
