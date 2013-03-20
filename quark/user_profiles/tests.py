from django.test import TestCase

from quark.auth.models import User
from quark.shortcuts import get_object_or_none
from quark.user_profiles.models import CollegeStudentInfo
from quark.user_profiles.models import TBPProfile
from quark.user_profiles.models import UserContactInfo


class TBPProfilesTest(TestCase):
    def setUp(self):
        self.model = TBPProfile

        self.user = User.objects.create_user(
            'test_user', 'it@tbp.berkeley.edu', 'testpw', 'Edward', 'Williams')

        self.profile = TBPProfile(user=self.user)
        self.profile.save()

    def test_tbp_profile_post_save(self):
        """Tests whether creating and saving a TBPProfile properly ensures that
        CollegeStudentInfo and UserContactInfo objects exist for the user in
        the post_save callback.
        """
        self.assertIsNotNone(get_object_or_none(CollegeStudentInfo,
                                                user=self.user))
        self.assertIsNotNone(get_object_or_none(UserContactInfo,
                                                user=self.user))
