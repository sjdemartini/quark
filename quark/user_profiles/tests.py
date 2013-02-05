from django.test import TestCase

from quark.auth.models import User
from quark.base.models import Officer
from quark.base.models import OfficerPosition
from quark.base.models import Term
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

        self.committee = OfficerPosition(
            position_type=OfficerPosition.TBP_OFFICER,
            short_name='it',
            long_name='Information Technology (test)',
            rank=2,
            mailing_list='IT')
        self.committee.save()

        self.house_leader = OfficerPosition(
            position_type=OfficerPosition.TBP_OFFICER,
            short_name='house-leader',
            long_name='House Leader (test)',
            rank=3,
            mailing_list='IT')
        self.house_leader.save()

        self.advisor_pos = OfficerPosition(
            position_type=OfficerPosition.TBP_OFFICER,
            short_name='advisor',
            long_name='Advisor (test)',
            rank=4,
            mailing_list='IT')
        self.advisor_pos.save()

        self.term = Term(term=Term.SPRING, year=2013, current=True)
        self.term.save()
        self.term_old = Term(term=Term.SPRING, year=2012)
        self.term_old.save()

    def test_is_officer(self):
        self.assertFalse(self.profile.is_officer())

        Officer(user=self.user, position=self.committee, term=self.term,
                is_chair=True).save()
        self.assertTrue(self.profile.is_officer())

    def test_is_current_officer(self):
        # Note that is_current_officer also tests get_officer_positions()
        self.assertFalse(self.profile.is_current_officer())

        officer = Officer(user=self.user, position=self.committee,
                          term=self.term, is_chair=True)
        officer.save()
        self.assertTrue(self.profile.is_current_officer())
        self.assertTrue(self.profile.is_current_officer(self.term))
        self.assertFalse(self.profile.is_current_officer(self.term_old))

        officer.term = self.term_old
        officer.save()
        self.assertFalse(self.profile.is_current_officer())
        self.assertFalse(self.profile.is_current_officer(self.term))
        self.assertTrue(self.profile.is_current_officer(self.term_old))

        officer.position = self.advisor_pos
        officer.term = self.term
        officer.save()
        self.assertTrue(self.profile.is_current_officer())
        self.assertTrue(self.profile.is_current_officer(self.term))
        self.assertFalse(self.profile.is_current_officer(self.term_old))

        # Exclude auxiliary positions, such as advisors:
        self.assertFalse(self.profile.is_current_officer(exclude_aux=True))
        self.assertFalse(self.profile.is_current_officer(self.term,
                                                         exclude_aux=True))
        self.assertFalse(self.profile.is_current_officer(self.term_old,
                                                         exclude_aux=True))

        # Test 'house-leader' pre and post Fall 2012:
        officer.position = self.house_leader
        officer.term = self.term_old
        officer.save()
        # officer.term is before Fa12, so house-leader is an auxiliary officer
        self.assertFalse(self.profile.is_current_officer(self.term))
        self.assertTrue(self.profile.is_current_officer(self.term_old))
        self.assertFalse(self.profile.is_current_officer(self.term_old,
                                                         exclude_aux=True))
        # officer.term is later than Fa12, so house-leader is a true officer
        officer.term = self.term
        officer.save()
        self.assertTrue(self.profile.is_current_officer(self.term))
        self.assertFalse(self.profile.is_current_officer(self.term_old))
        self.assertTrue(self.profile.is_current_officer(self.term,
                                                        exclude_aux=True))

    def test_get_officer_positions(self):
        # Note that when given no 'term' kwarg, the method returns positions
        # from all terms. The order of the list returned is based on term, then
        # officer position rank
        # No officer positions for this user yet:
        self.assertEqual(self.profile.get_officer_positions(), [])

        Officer(user=self.user, position=self.committee, term=self.term,
                is_chair=True).save()
        self.assertEqual(
            self.profile.get_officer_positions(),
            [self.committee])
        self.assertEqual(
            self.profile.get_officer_positions(term=self.term),
            [self.committee])
        self.assertEqual(
            self.profile.get_officer_positions(term=self.term_old),
            [])

        Officer(user=self.user, position=self.advisor_pos,
                term=self.term_old).save()
        self.assertEqual(
            self.profile.get_officer_positions(),
            [self.advisor_pos, self.committee])
        self.assertEqual(
            self.profile.get_officer_positions(term=self.term),
            [self.committee])
        self.assertEqual(
            self.profile.get_officer_positions(term=self.term_old),
            [self.advisor_pos])

        Officer(user=self.user, position=self.advisor_pos,
                term=self.term).save()
        self.assertEqual(
            self.profile.get_officer_positions(),
            [self.advisor_pos, self.committee, self.advisor_pos])
        self.assertEqual(
            self.profile.get_officer_positions(term=self.term),
            [self.committee, self.advisor_pos])
        self.assertEqual(
            self.profile.get_officer_positions(term=self.term_old),
            [self.advisor_pos])

        # Ensure ordering is correct:
        Officer(user=self.user, position=self.house_leader,
                term=self.term).save()
        self.assertEqual(
            self.profile.get_officer_positions(),
            [self.advisor_pos, self.committee, self.house_leader,
             self.advisor_pos])
        older_term = Term(term=Term.SPRING, year=2008)
        older_term.save()
        Officer(user=self.user, position=self.house_leader,
                term=older_term).save()
        self.assertEqual(
            self.profile.get_officer_positions(),
            [self.house_leader, self.advisor_pos, self.committee,
             self.house_leader, self.advisor_pos])

    def test_is_position(self):
        self.assertFalse(self.profile.is_position('it'))
        self.assertFalse(self.profile.is_position('advisor'))
        Officer(user=self.user, position=self.committee, term=self.term,
                is_chair=True).save()
        self.assertTrue(self.profile.is_position('it'))

        Officer(user=self.user, position=self.advisor_pos,
                term=self.term_old).save()
        self.assertTrue(self.profile.is_position('it'))
        self.assertTrue(self.profile.is_position('advisor'))

    def test_get_preferred_email(self):
        self.assertEqual(self.profile.get_preferred_email(), self.user.email)

        # With an alternate email address in the contact info profile:
        contact_info = get_object_or_none(UserContactInfo, user=self.user)
        test_email = 'test_' + self.user.email
        contact_info.alt_email = test_email
        contact_info.save()

        # QuarkUser email (if not empty) is still preferred over alt_email:
        self.assertEqual(self.profile.get_preferred_email(), self.user.email)

        # Remove user email, keeping alternate email:
        self.user.email = ''
        self.user.save()
        self.assertEqual(self.profile.get_preferred_email(), test_email)

        Officer(user=self.user, position=self.committee, term=self.term,
                is_chair=True).save()
        self.assertEqual(self.profile.get_preferred_email(),
                         '%s@tbp.berkeley.edu' % self.user.username)

    def test_tbp_profile_post_save(self):
        """Tests whether creating and saving a TBPProfile properly ensures that
        CollegeStudentInfo and UserContactInfo objects exist for the user in
        the post_save callback.
        """
        self.assertIsNotNone(get_object_or_none(CollegeStudentInfo,
                                                user=self.user))
        self.assertIsNotNone(get_object_or_none(UserContactInfo,
                                                user=self.user))
