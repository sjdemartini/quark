from chosen import forms


def user_common_name_label(obj):
    """Return the common name label for a given object."""
    try:
        # Try getting the UserProfile as a reverse one-to-one relation, and
        # call its get_common_name method if available
        return obj.userprofile.get_common_name()
    except AttributeError:  # If no user profile available
        pass

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
