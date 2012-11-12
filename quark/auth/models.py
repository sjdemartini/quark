from django.db.models import get_model

from quark.settings import AUTH_USER_MODEL


# Placeholder for Django 1.5's django.contrib.auth.get_user_model()
def get_user_model(model=AUTH_USER_MODEL):
    user = get_model(*model.split('.', 1))
    if user is None:
        raise NameError('User model not found: %s' % model)
    return user


# pylint: disable-msg=C0103
User = get_user_model()
