from django.contrib.auth import get_user_model
from django.test import TestCase

from quark.achievements.models import Achievement
from quark.achievements.models import UserAchievement
from quark.base.models import Term
from quark.base_tbp.models import Officer
from quark.base_tbp.models import OfficerPosition


class AchievementAssignmentTest(TestCase):
    fixtures = ['term.yaml']

    def setUp(self):
        self.sample_user = get_user_model().objects.create_user(
            username='test', password='test', email='test@tbp.berkeley.edu',
            first_name="Test", last_name="Test")
        self.achievement, _ = Achievement.objects.get_or_create(
            name='test_achievement', pk='test',
            description='test', points=0, goal=0, privacy='public',
            category='feats')
        self.achievements = UserAchievement.objects.filter(
            user=self.sample_user)

        self.fa2009 = Term.objects.get(term='fa', year='2009')
        self.sp2010 = Term.objects.get(term='sp', year='2010')
        self.fa2010 = Term.objects.get(term='fa', year='2010')

    def test_assignment(self):
        # test to see that assigning the achievement creates an achievement
        # object in the database
        self.assertEqual(self.achievements.filter(
            achievement__pk='test').count(), 0)
        Achievement.objects.get(pk='test').assign(
            self.sample_user, acquired=False)
        self.assertEqual(self.achievements.filter(
            achievement__pk='test').count(), 1)
        self.assertEqual(self.achievements.filter(
            achievement__pk='test', acquired=True).count(), 0)

        self.assertEqual(self.achievements.filter(
            achievement__pk='test', acquired=True).count(), 0)
        Achievement.objects.get(pk='test').assign(
            self.sample_user, acquired=True)
        self.assertEqual(self.achievements.filter(
            achievement__pk='test', acquired=True).count(), 1)

    def test_update(self):
        # test to see that an achievement can be reset to not acquired and
        # that progress can be updated successfully
        Achievement.objects.get(pk='test').assign(
            self.sample_user, acquired=True)
        Achievement.objects.get(pk='test').assign(
            self.sample_user, acquired=False, progress=1)

        self.assertEqual(self.achievements.filter(
            achievement__pk='test', acquired=True).count(), 0)

        Achievement.objects.get(pk='test').assign(
            self.sample_user, acquired=False, progress=2)

        self.assertEqual(self.achievements.filter(
            achievement__pk='test', acquired=True).count(), 0)
        user_achievement = UserAchievement.objects.get(
            achievement__pk='test', user=self.sample_user)
        self.assertEqual(user_achievement.progress, 2)

    def test_first_term_stays_with_achievement(self):
        # test to make sure that getting the achievement in two different
        # semesters will keep the term as the first term in which the user
        # obtained it.

        Achievement.objects.get(pk='test').assign(
            self.sample_user, acquired=False, term=self.fa2009)
        Achievement.objects.get(pk='test').assign(
            self.sample_user, acquired=True, term=self.sp2010)

        # since the first achievement was just progress, the term will
        # be the first term where it was acquired - spring 2010
        self.assertEqual(self.achievements.filter(term=self.sp2010).count(), 1)

        Achievement.objects.get(pk='test').assign(
            self.sample_user, acquired=True, term=self.fa2010)
        # since the achievement has already been acquired earlier, it
        # should retain the original term
        self.assertEqual(self.achievements.filter(term=self.sp2010).count(), 1)
        self.assertEqual(self.achievements.filter(term=self.fa2010).count(), 0)

    def test_terms_after_acquiring_dont_overwrite(self):
        # test to ensure that after receiving an achievement it will not be
        # overwritten if progress is obtained in a different semester

        Achievement.objects.get(pk='test').assign(
            self.sample_user, acquired=True, term=self.sp2010)

        Achievement.objects.get(pk='test').assign(
            self.sample_user, acquired=False, progress=1, term=self.fa2010)
        # since the achievement was acquired in a previous semester, it should
        # not be overwritten by progress acquired in another term
        self.assertEqual(self.achievements.filter(term=self.sp2010).count(), 1)
        self.assertEqual(self.achievements.filter(acquired=True).count(), 1)


class OfficerAchievementsTest(TestCase):
    fixtures = ['achievement.yaml',
                'term.yaml',
                'officer_position.yaml']

    def setUp(self):
        self.sample_user = get_user_model().objects.create_user(
            username='test', password='test', email='test@tbp.berkeley.edu',
            first_name="Test", last_name="Test")
        self.achievements = UserAchievement.objects.filter(
            user=self.sample_user)

        self.sp2009 = Term.objects.get(term='sp', year=2009)
        self.fa2009 = Term.objects.get(term='fa', year=2009)
        self.sp2010 = Term.objects.get(term='sp', year=2010)
        self.fa2010 = Term.objects.get(term='fa', year=2010)
        self.sp2011 = Term.objects.get(term='sp', year=2011)
        self.fa2011 = Term.objects.get(term='fa', year=2011)
        self.sp2012 = Term.objects.get(term='sp', year=2012)
        self.fa2012 = Term.objects.get(term='fa', year=2012)
        self.sp2013 = Term.objects.get(term='sp', year=2013)
        self.fa2013 = Term.objects.get(term='fa', year=2013)

        self.house_leader = OfficerPosition.objects.get(
            short_name='house-leaders')
        self.historian = OfficerPosition.objects.get(short_name='historian')
        self.infotech = OfficerPosition.objects.get(short_name='it')
        self.vicepres = OfficerPosition.objects.get(short_name='vp')

    def create_officer(self, user, position, term=None, is_chair=False):
        if term is None:
            term = self.fa2013
        Officer.objects.get_or_create(user=user, position=position, term=term,
                                      is_chair=is_chair)

    def test_number_of_officer_semesters(self):
        # first officer semester
        self.assertEqual(self.achievements.filter(
            achievement__pk='officersemester01').count(), 0)
        self.assertEqual(self.achievements.filter(
            achievement__pk='officersemester08').count(), 0)
        self.create_officer(self.sample_user, self.historian, self.sp2009)
        self.assertEqual(self.achievements.filter(
            achievement__pk='officersemester01').count(), 1)
        self.assertEqual(self.achievements.filter(
            achievement__pk='officersemester08').count(), 1)

        self.assertEqual(self.achievements.filter(
            achievement__pk='officersemester01', acquired=True).count(), 1)
        self.assertEqual(self.achievements.filter(
            achievement__pk='officersemester02', acquired=True).count(), 0)
        self.assertEqual(self.achievements.filter(
            achievement__pk='officersemester03', acquired=True).count(), 0)
        self.assertEqual(self.achievements.filter(
            achievement__pk='officersemester04', acquired=True).count(), 0)
        self.assertEqual(self.achievements.filter(
            achievement__pk='officersemester05', acquired=True).count(), 0)
        self.assertEqual(self.achievements.filter(
            achievement__pk='officersemester06', acquired=True).count(), 0)
        self.assertEqual(self.achievements.filter(
            achievement__pk='officersemester07', acquired=True).count(), 0)
        self.assertEqual(self.achievements.filter(
            achievement__pk='officersemester08', acquired=True).count(), 0)

    def test_second_officer_term(self):
        # second officer semester gets second achievement
        self.create_officer(self.sample_user, self.historian, self.sp2009)
        self.create_officer(self.sample_user, self.vicepres, self.fa2009)
        self.assertEqual(self.achievements.filter(
            achievement__pk='officersemester02', acquired=True).count(), 1)
        self.assertEqual(self.achievements.filter(
            achievement__pk='officersemester03', acquired=True).count(), 0)
        threeachievement = UserAchievement.objects.get(
            achievement__pk='officersemester03', user=self.sample_user)
        self.assertEqual(threeachievement.progress, 2)

    def test_multiple_positions_same_semester(self):
        # two officer positions in same semester don't give achievement
        self.create_officer(self.sample_user, self.historian, self.fa2009)
        self.create_officer(self.sample_user, self.infotech, self.fa2009)
        self.assertEqual(self.achievements.filter(
            achievement__pk='officersemester01', acquired=True).count(), 1)
        self.assertEqual(self.achievements.filter(
            achievement__pk='officersemester02', acquired=True).count(), 0)
        fiveachievement = UserAchievement.objects.get(
            achievement__pk='officersemester05', user=self.sample_user)
        self.assertEqual(fiveachievement.progress, 1)
