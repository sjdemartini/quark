from django.contrib.auth.models import User
from django.test import TestCase

from quark.auth.models import get_user_model


class UserModelTest(TestCase):
    def get_correct_user_model(self):
        self.assertEqual(get_user_model('auth.User'), User)
        self.assertRaises(NameError, get_user_model, 'nonexistent.User')
