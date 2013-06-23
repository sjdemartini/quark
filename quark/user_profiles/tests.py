from django.contrib.auth import get_user_model
from django.test import TestCase

from quark.base.models import Term
from quark.candidates.models import Candidate
from quark.shortcuts import get_object_or_none
from quark.user_profiles.models import CollegeStudentInfo
from quark.user_profiles.models import TBPProfile
from quark.user_profiles.models import UserContactInfo


class TBPProfilesTest(TestCase):
    def setUp(self):
        self.model = TBPProfile

        self.user = get_user_model().objects.create_user(
            'test_user', 'it@tbp.berkeley.edu', 'testpw', 'Edward', 'Williams')

        self.profile = TBPProfile(user=self.user)
        self.profile.save()

        self.term = Term(term=Term.SPRING, year=2013, current=True)
        self.term.save()
        self.term_old = Term(term=Term.SPRING, year=2012)
        self.term_old.save()

    def test_is_candidate(self):
        # No Candidate objects created yet:
        self.assertFalse(self.profile.is_candidate())

        # Create Candidate for user in a past term:
        candidate = Candidate(user=self.user, term=self.term_old)
        candidate.save()
        # Should now be considered a candidate only if current=False:
        self.assertTrue(self.profile.is_candidate(current=False))
        self.assertFalse(self.profile.is_candidate(current=True))

        # Mark that candidate as initiated:
        candidate.initiated = True
        candidate.save()
        # Re-fetch profile since candidate save affects TBPProfile
        # initiation_term field:
        self.profile = get_object_or_none(TBPProfile, user=self.user)
        self.assertFalse(self.profile.is_candidate(current=False))
        self.assertFalse(self.profile.is_candidate(current=True))

        # Mark initiated as False, and create new Candidate for the current
        # Term, as is the case for a candidate who doesn't initiate one term
        # and returns as a candidate a later term:
        candidate.initiated = False
        candidate.save()
        candidate = Candidate(user=self.user, term=self.term)
        candidate.save()
        self.profile = get_object_or_none(TBPProfile, user=self.user)
        # Should be now considered a candidate (initiated not True):
        self.assertTrue(self.profile.is_candidate(current=False))
        self.assertTrue(self.profile.is_candidate(current=True))

        # Mark that candidate as initiated:
        candidate.initiated = True
        candidate.save()
        self.profile = get_object_or_none(TBPProfile, user=self.user)
        self.assertFalse(self.profile.is_candidate(current=False))
        self.assertFalse(self.profile.is_candidate(current=True))

        # Change the 'current' semester to an old semester:
        self.term_old.current = True
        self.term_old.save()
        # Now the candidate should be considered a candidate since they have
        # not _yet_ initiated based on what the current semester is, but
        # they are in the database as a candidate for the current semester:
        self.assertTrue(self.profile.is_candidate(current=False))
        self.assertTrue(self.profile.is_candidate(current=True))

        # Ensure that they are also marked as a candidate if initiated = False
        candidate.initiated = False
        candidate.save()
        self.profile = get_object_or_none(TBPProfile, user=self.user)
        self.assertTrue(self.profile.is_candidate(current=False))
        self.assertTrue(self.profile.is_candidate(current=True))

    def test_get_first_term_as_candidate(self):
        # No Candidate objects created yet:
        self.assertFalse(self.profile.is_candidate())
        self.assertIsNone(self.profile.get_first_term_as_candidate())

        # Create Candidate for user in a past term:
        candidate = Candidate(user=self.user, term=self.term_old)
        candidate.save()
        self.assertEqual(self.profile.get_first_term_as_candidate(),
                         self.term_old)

        # Create Candidate for user in current term, and past term should
        # still be marked as first term as candidate:
        candidate = Candidate(user=self.user, term=self.term)
        candidate.save()
        self.assertEqual(self.profile.get_first_term_as_candidate(),
                         self.term_old)

        # Create user who only has initiation term data and no Candidate
        # objects:
        temp_user = get_user_model().objects.create_user(
            'tester', 'test@tbp.berkeley.edu', 'testpw', 'Bentley', 'Bent')
        temp_user.save()

        profile = TBPProfile(user=temp_user)
        profile.save()
        self.assertIsNone(profile.get_first_term_as_candidate())

        profile.initiation_term = self.term
        profile.save()
        self.assertEqual(profile.get_first_term_as_candidate(),
                         self.term)

    def test_tbp_profile_post_save(self):
        """Tests whether creating and saving a TBPProfile properly ensures that
        CollegeStudentInfo and UserContactInfo objects exist for the user in
        the post_save callback.
        """
        self.assertIsNotNone(get_object_or_none(CollegeStudentInfo,
                                                user=self.user))
        self.assertIsNotNone(get_object_or_none(UserContactInfo,
                                                user=self.user))
