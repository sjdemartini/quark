import random
import string

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from quark.achievements.models import Achievement
from quark.achievements.models import UserAchievement
from quark.base.models import Officer
from quark.base.models import OfficerPosition
from quark.base.models import Term
from quark.events.models import Event
from quark.events.models import EventAttendance
from quark.events.models import EventType


class AchievementAssignmentTest(TestCase):
    fixtures = ['test/term.yaml']

    def setUp(self):
        self.sample_user = get_user_model().objects.create_user(
            username='test', password='test', email='test@tbp.berkeley.edu',
            first_name="Test", last_name="Test")
        self.achievement, _ = Achievement.objects.get_or_create(
            name='test_achievement', short_name='test',
            description='test', points=0, goal=0, privacy='public',
            category='feats')
        self.achievements = UserAchievement.objects.filter(
            user=self.sample_user)

        self.fa2009 = Term.objects.get(term=Term.FALL, year='2009')
        self.sp2010 = Term.objects.get(term=Term.SPRING, year='2010')
        self.fa2010 = Term.objects.get(term=Term.FALL, year='2010')

    def test_assignment(self):
        # test to see that assigning the achievement creates an achievement
        # object in the database
        self.assertEqual(self.achievements.filter(
            achievement__short_name='test').count(), 0)
        Achievement.objects.get(short_name='test').assign(
            self.sample_user, acquired=False)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='test').count(), 1)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='test', acquired=True).count(), 0)

        self.assertEqual(self.achievements.filter(
            achievement__short_name='test', acquired=True).count(), 0)
        Achievement.objects.get(short_name='test').assign(
            self.sample_user, acquired=True)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='test', acquired=True).count(), 1)

    def test_update(self):
        # test to see that an achievement can be reset to not acquired and
        # that progress can be updated successfully
        Achievement.objects.get(short_name='test').assign(
            self.sample_user, acquired=True)
        Achievement.objects.get(short_name='test').assign(
            self.sample_user, acquired=False, progress=1)

        self.assertEqual(self.achievements.filter(
            achievement__short_name='test', acquired=True).count(), 0)

        Achievement.objects.get(short_name='test').assign(
            self.sample_user, acquired=False, progress=2)

        self.assertEqual(self.achievements.filter(
            achievement__short_name='test', acquired=True).count(), 0)
        user_achievement = UserAchievement.objects.get(
            achievement__short_name='test', user=self.sample_user)
        self.assertEqual(user_achievement.progress, 2)

    def test_first_term_stays_with_achievement(self):
        # test to make sure that getting the achievement in two different
        # semesters will keep the term as the first term in which the user
        # obtained it.

        Achievement.objects.get(short_name='test').assign(
            self.sample_user, acquired=False, term=self.fa2009)
        Achievement.objects.get(short_name='test').assign(
            self.sample_user, acquired=True, term=self.sp2010)

        # since the first achievement was just progress, the term will
        # be the first term where it was acquired - spring 2010
        self.assertEqual(self.achievements.filter(term=self.sp2010).count(), 1)

        Achievement.objects.get(short_name='test').assign(
            self.sample_user, acquired=True, term=self.fa2010)
        # since the achievement has already been acquired earlier, it
        # should retain the original term
        self.assertEqual(self.achievements.filter(term=self.sp2010).count(), 1)
        self.assertEqual(self.achievements.filter(term=self.fa2010).count(), 0)

    def test_terms_after_acquiring_dont_overwrite(self):
        # test to ensure that after receiving an achievement it will not be
        # overwritten if progress is obtained in a different semester

        Achievement.objects.get(short_name='test').assign(
            self.sample_user, acquired=True, term=self.sp2010)

        Achievement.objects.get(short_name='test').assign(
            self.sample_user, acquired=False, progress=1, term=self.fa2010)
        # since the achievement was acquired in a previous semester, it should
        # not be overwritten by progress acquired in another term
        self.assertEqual(self.achievements.filter(term=self.sp2010).count(), 1)
        self.assertEqual(self.achievements.filter(acquired=True).count(), 1)


class EventAchievementsTest(TestCase):
    fixtures = ['achievement.yaml',
                'officer_position.yaml',
                'test/term.yaml']

    def setUp(self):
        self.sample_user = get_user_model().objects.create_user(
            username='test', password='test', email='test@tbp.berkeley.edu',
            first_name="Test", last_name="Test")
        self.achievements = UserAchievement.objects.filter(
            user=self.sample_user)

        self.sp2012 = Term.objects.get(term=Term.SPRING, year='2012')
        self.fa2012 = Term.objects.get(term=Term.FALL, year='2012')
        self.sp2013 = Term.objects.get(term=Term.SPRING, year='2013')
        self.fa2013 = Term.objects.get(term=Term.FALL, year='2013')

        self.bent, _ = EventType.objects.get_or_create(name="Bent Polishing")
        self.big_social, _ = EventType.objects.get_or_create(name="Big Social")
        self.prodev, _ = EventType.objects.get_or_create(
            name="Professional Development")
        self.service, _ = EventType.objects.get_or_create(
            name="Community Service")
        self.efutures, _ = EventType.objects.get_or_create(name="E Futures")
        self.fun, _ = EventType.objects.get_or_create(name="Fun")
        self.meeting, _ = EventType.objects.get_or_create(name="Meeting")
        self.info, _ = EventType.objects.get_or_create(name="Infosession")

    def create_event(self, event_type, name=None, term=None, attendance=True):
        if name is None:
            name = ''.join(
                random.choice(string.ascii_uppercase) for x in range(6))
        if term is None:
            term = self.sp2013

        event, _ = Event.objects.get_or_create(
            name=name,
            contact=self.sample_user,
            term=term,
            location="TBD",
            event_type=event_type,
            start_datetime=timezone.now(),
            end_datetime=timezone.now(),
            committee=OfficerPosition.objects.first())

        if attendance:
            EventAttendance.objects.get_or_create(event=event,
                                                  user=self.sample_user)

        return event

    def create_many_events(self, number, event_type, term=None,
                           attendance=True):
        if term is None:
            term = self.sp2013

        events = [Event(
            name='Event{:03d}'.format(i),
            event_type=event_type,
            term=term,
            contact=self.sample_user,
            location="TBD",
            start_datetime=timezone.now(),
            end_datetime=timezone.now(),
            committee=OfficerPosition.objects.first())
            for i in range(0, number)]

        Event.objects.bulk_create(events)

        if attendance:
            created_events = Event.objects.order_by('-created')[:number]
            attendances = [EventAttendance(user=self.sample_user, event=event)
                           for event in created_events]
            EventAttendance.objects.bulk_create(attendances)

    def test_25_lifetime_events(self):
        """Achievement for 25 lifetime events is obtained after 25th event.
        """
        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend025events').count(), 0)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend050events').count(), 0)

        self.create_many_events(23, event_type=self.fun, term=self.sp2012)
        self.create_event(event_type=self.fun, term=self.sp2012)

        twentyfive_achievement = UserAchievement.objects.get(
            achievement__short_name='attend025events', user=self.sample_user)
        self.assertFalse(twentyfive_achievement.acquired)
        self.assertEqual(twentyfive_achievement.progress, 24)

        self.create_event(event_type=self.fun, term=self.sp2012)

        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend025events',
            acquired=True).count(), 1)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend050events',
            acquired=False).count(), 1)

    def test_50_lifetime_events(self):
        """Achievement for 50 lifetime events is obtained after 50th event.
        """
        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend050events').count(), 0)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend078events').count(), 0)

        self.create_many_events(48, event_type=self.fun, term=self.sp2012)
        self.create_event(event_type=self.fun, term=self.sp2012)

        fifty_achievement = UserAchievement.objects.get(
            achievement__short_name='attend050events', user=self.sample_user)
        self.assertFalse(fifty_achievement.acquired)
        self.assertEqual(fifty_achievement.progress, 49)

        self.create_event(event_type=self.fun, term=self.sp2012)

        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend050events',
            acquired=True).count(), 1)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend078events',
            acquired=False).count(), 1)

    def test_78_lifetime_events(self):
        """Achievement for 78 lifetime events is obtained after the 78th event.
        """
        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend078events').count(), 0)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend100events').count(), 0)

        self.create_many_events(76, event_type=self.fun, term=self.sp2012)
        self.create_event(event_type=self.fun, term=self.sp2012)

        seventyeight_achievement = UserAchievement.objects.get(
            achievement__short_name='attend078events', user=self.sample_user)
        self.assertFalse(seventyeight_achievement.acquired)
        self.assertEqual(seventyeight_achievement.progress, 77)

        self.create_event(event_type=self.fun, term=self.sp2012)

        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend078events',
            acquired=True).count(), 1)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend100events',
            acquired=False).count(), 1)

    def test_100_lifetime_events(self):
        """Achievement for 100 lifetime events is obtained after 100th event.
        """
        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend100events').count(), 0)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend150events').count(), 0)

        self.create_many_events(98, event_type=self.fun, term=self.sp2012)
        self.create_event(event_type=self.fun, term=self.sp2012)

        hundred_achievement = UserAchievement.objects.get(
            achievement__short_name='attend100events', user=self.sample_user)
        self.assertFalse(hundred_achievement.acquired)
        self.assertEqual(hundred_achievement.progress, 99)

        self.create_event(event_type=self.fun, term=self.sp2012)

        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend100events',
            acquired=True).count(), 1)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend150events',
            acquired=False).count(), 1)

    def test_150_lifetime_events(self):
        """Achievement for 150 lifetime events is obtained after 150th event.
        """
        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend150events').count(), 0)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend200events').count(), 0)

        self.create_many_events(148, event_type=self.fun, term=self.sp2012)
        self.create_event(event_type=self.fun, term=self.sp2012)

        onefifty_achievement = UserAchievement.objects.get(
            achievement__short_name='attend150events', user=self.sample_user)
        self.assertFalse(onefifty_achievement.acquired)
        self.assertEqual(onefifty_achievement.progress, 149)

        self.create_event(event_type=self.fun, term=self.sp2012)

        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend150events',
            acquired=True).count(), 1)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend200events',
            acquired=False).count(), 1)

    def test_200_lifetime_events(self):
        """Achievement for 200 lifetime events is obtained after 200th event.
        """
        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend200events').count(), 0)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend300events').count(), 0)

        self.create_many_events(198, event_type=self.fun, term=self.sp2012)
        self.create_event(event_type=self.fun, term=self.sp2012)

        twohundred_achievement = UserAchievement.objects.get(
            achievement__short_name='attend200events', user=self.sample_user)
        self.assertFalse(twohundred_achievement.acquired)
        self.assertEqual(twohundred_achievement.progress, 199)

        self.create_event(event_type=self.fun, term=self.sp2012)

        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend200events',
            acquired=True).count(), 1)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend300events',
            acquired=False).count(), 1)

    def test_300_lifetime_events(self):
        """Achievement for 300 lifetime events is obtained after 300th events.
        """
        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend300events').count(), 0)

        self.create_many_events(298, event_type=self.fun, term=self.sp2012)
        self.create_event(event_type=self.fun, term=self.sp2012)

        threehundred_achievement = UserAchievement.objects.get(
            achievement__short_name='attend300events', user=self.sample_user)
        self.assertFalse(threehundred_achievement.acquired)
        self.assertEqual(threehundred_achievement.progress, 299)

        self.create_event(event_type=self.fun, term=self.sp2012)

        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend300events',
            acquired=True).count(), 1)

    def test_lifetime_events_with_different_terms(self):
        """Achievements for lifetime events can be obtained by attending
        events in multiple different semesters.
        """
        self.create_many_events(24, event_type=self.fun, term=self.sp2012)
        self.create_event(event_type=self.fun, term=self.fa2012)

        achievement = UserAchievement.objects.get(
            achievement__short_name='attend025events', user=self.sample_user)
        self.assertTrue(achievement.acquired)
        self.assertEqual(achievement.term, self.fa2012)

    def test_lifetime_events_backfill(self):
        """Achievements for lifetime event attendance are awarded for the 25th
        event attended in real life, not the 25th object added to the DB.
        """
        self.create_many_events(23, event_type=self.bent, term=self.sp2013)
        self.create_event(event_type=self.prodev, term=self.sp2013)
        achievement = UserAchievement.objects.get(
            achievement__short_name='attend025events', user=self.sample_user)
        self.assertEqual(achievement.progress, 24)

        self.create_event(name='Event025',
                          event_type=self.fun, term=self.sp2012)

        achievement = UserAchievement.objects.get(
            achievement__short_name='attend025events', user=self.sample_user)

        self.assertTrue(achievement.acquired)
        self.assertEqual(achievement.term, self.sp2013)

    def test_salad_bowl(self):
        """The achievement for attending one event of each type in a semester
        may be awarded after missing an event of one type if an event of the
        same type is attended later in the semester.
        """
        self.create_event(name='Fun', event_type=self.fun, attendance=False)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend_each_type',
            acquired=True).count(), 0)

        self.create_event(name='Bent', event_type=self.bent)
        self.create_event(name='Service', event_type=self.service)
        self.create_event(name='ProDev', event_type=self.prodev)
        self.create_event(name='Meeting', event_type=self.meeting)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend_each_type',
            acquired=True).count(), 0)

        self.create_event(name='Fun2', event_type=self.fun, attendance=True)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend_each_type',
            acquired=True).count(), 1)

    def test_event_type_achievement(self):
        """The achievement for attending all events of a certain type in one
        semester can be awarded by attending all fun events, for example, in
        a later semester after not attending all in a previous semester.
        """
        self.create_event(name='Fun1',
                          event_type=self.fun,
                          attendance=False,
                          term=self.sp2012)
        self.create_event(name='Fun2',
                          event_type=self.fun,
                          attendance=True,
                          term=self.sp2012)

        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend_all_fun', acquired=True).count(), 0)

        self.create_event(name='Fun3',
                          event_type=self.fun,
                          attendance=True,
                          term=self.fa2012)
        achievement = UserAchievement.objects.get(
            achievement__short_name='attend_all_fun', user=self.sample_user)
        self.assertTrue(achievement.acquired)
        self.assertEqual(achievement.term, self.fa2012)

    def test_d15_achievement(self):
        """The achievement for attending District 15 Conference is given
        for a member who attends an event titled D15.
        """
        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend_d15', acquired=True).count(), 0)

        self.create_event(name="D16", event_type=self.meeting)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend_d15', acquired=True).count(), 0)

        self.create_event(name="D15", event_type=self.meeting,
                          attendance=False)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend_d15', acquired=True).count(), 0)

        self.create_event(name="D15", event_type=self.meeting)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend_d15', acquired=True).count(), 1)

    def test_d15_alt(self):
        """The D15 achievement can also be given for attending an event titled
        District 15 Conference.
        """
        self.create_event(name="District 15 Conference", event_type=self.fun)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend_d15', acquired=True).count(), 1)

    def test_d15_alt2(self):
        """The D15 achievement can also be given for attending an event that
        includes the string 'D 15', such as D 15 Convention.
        """
        self.create_event(name="D 15 Convention", event_type=self.big_social)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend_d15', acquired=True).count(), 1)

    def test_natl_convention_achievement(self):
        """The achievement for attending National Convention is awarded for
        attending an event where the title includes the phrase:
        'National Convention'
        """
        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend_convention',
            acquired=True).count(), 0)

        self.create_event(name="D15 Convention", event_type=self.fun)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend_convention',
            acquired=True).count(), 0)

        self.create_event(name="National Convention", event_type=self.fun,
                          attendance=False)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend_convention',
            acquired=True).count(), 0)

        self.create_event(name="National Convention", event_type=self.fun)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='attend_convention',
            acquired=True).count(), 1)

    def test_berkeley_explosion_achievement(self):
        """The achievement for attending the Berkeley Explosion CM is awarded
        only for attending an event titled exactly 'Candidate Meeting' in the
        Fall 2013 term.
        """
        self.assertEqual(self.achievements.filter(
            achievement__short_name='berkeley_explosion',
            acquired=True).count(), 0)

        self.create_event(name="Candidate Meeting", event_type=self.meeting,
                          term=self.sp2012)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='berkeley_explosion',
            acquired=True).count(), 0)

        self.create_event(name="Candidate Meeting 2", event_type=self.meeting,
                          term=self.fa2013)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='berkeley_explosion',
            acquired=True).count(), 0)

        self.create_event(name="Candidate Meeting", event_type=self.meeting,
                          term=self.fa2013, attendance=False)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='berkeley_explosion',
            acquired=True).count(), 0)

        self.create_event(name="Candidate Meeting", event_type=self.meeting,
                          term=self.fa2013, attendance=True)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='berkeley_explosion',
            acquired=True).count(), 1)

    def test_alphabet_attendance_achievement(self):
        """The achievement for attending events with all the letters of the
        alphabet in the titles is awarded for such, ignoring capitalization.
        """
        self.assertEqual(self.achievements.filter(
            achievement__short_name='alphabet_attendance',
            acquired=True).count(), 0)

        self.create_event(name="abcdefghijklm", event_type=self.fun)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='alphabet_attendance',
            acquired=True).count(), 0)

        self.create_event(name="NOPqrstuvwxyZ", event_type=self.meeting,
                          attendance=False)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='alphabet_attendance',
            acquired=True).count(), 0)

        self.create_event(name="noPqRstuvWxyz", event_type=self.info,
                          attendance=True)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='alphabet_attendance',
            acquired=True).count(), 1)


class OfficerAchievementsTest(TestCase):
    fixtures = ['achievement.yaml',
                'officer_position.yaml',
                'test/term.yaml']

    def setUp(self):
        self.sample_user = get_user_model().objects.create_user(
            username='test', password='test', email='test@tbp.berkeley.edu',
            first_name="Test", last_name="Test")
        self.achievements = UserAchievement.objects.filter(
            user=self.sample_user)

        self.sp2009 = Term.objects.get(term=Term.SPRING, year=2009)
        self.fa2009 = Term.objects.get(term=Term.FALL, year=2009)
        self.sp2010 = Term.objects.get(term=Term.SPRING, year=2010)
        self.fa2010 = Term.objects.get(term=Term.FALL, year=2010)
        self.sp2011 = Term.objects.get(term=Term.SPRING, year=2011)
        self.fa2011 = Term.objects.get(term=Term.FALL, year=2011)
        self.sp2012 = Term.objects.get(term=Term.SPRING, year=2012)
        self.fa2012 = Term.objects.get(term=Term.FALL, year=2012)
        self.sp2013 = Term.objects.get(term=Term.SPRING, year=2013)
        self.fa2013 = Term.objects.get(term=Term.FALL, year=2013)

        self.house_leader = OfficerPosition.objects.get(
            short_name='house-leaders')
        self.historian = OfficerPosition.objects.get(short_name='historian')
        self.infotech = OfficerPosition.objects.get(short_name='it')
        self.vicepres = OfficerPosition.objects.get(short_name='vp')
        self.president = OfficerPosition.objects.get(short_name='president')

    def create_officer(self, user, position, term=None, is_chair=False):
        if term is None:
            term = self.fa2013
        Officer.objects.get_or_create(user=user, position=position, term=term,
                                      is_chair=is_chair)

    def test_number_of_officer_semesters(self):
        # first officer semester
        self.assertEqual(self.achievements.filter(
            achievement__short_name='officersemester01').count(), 0)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='officersemester08').count(), 0)
        self.create_officer(self.sample_user, self.historian, self.sp2009)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='officersemester01').count(), 1)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='officersemester08').count(), 1)

        self.assertEqual(self.achievements.filter(
            achievement__short_name='officersemester01',
            acquired=True).count(), 1)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='officersemester02',
            acquired=True).count(), 0)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='officersemester03',
            acquired=True).count(), 0)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='officersemester04',
            acquired=True).count(), 0)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='officersemester05',
            acquired=True).count(), 0)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='officersemester06',
            acquired=True).count(), 0)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='officersemester07',
            acquired=True).count(), 0)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='officersemester08',
            acquired=True).count(), 0)

    def test_second_officer_term(self):
        # second officer semester gets second achievement
        self.create_officer(self.sample_user, self.historian, self.sp2009)
        self.create_officer(self.sample_user, self.vicepres, self.fa2009)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='officersemester02',
            acquired=True).count(), 1)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='officersemester03',
            acquired=True).count(), 0)
        threeachievement = UserAchievement.objects.get(
            achievement__short_name='officersemester03', user=self.sample_user)
        self.assertEqual(threeachievement.progress, 2)

    def test_multiple_positions_same_semester(self):
        # two officer positions in same semester don't give achievement
        self.create_officer(self.sample_user, self.historian, self.fa2009)
        self.create_officer(self.sample_user, self.infotech, self.fa2009)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='officersemester01',
            acquired=True).count(), 1)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='officersemester02',
            acquired=True).count(), 0)
        fiveachievement = UserAchievement.objects.get(
            achievement__short_name='officersemester05', user=self.sample_user)
        self.assertEqual(fiveachievement.progress, 1)

    def test_chair_semester(self):
        # being chair gives chair1committee
        self.create_officer(self.sample_user, self.historian, self.sp2009)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='chair1committee', acquired=True).count(),
            0)

        self.create_officer(self.sample_user, self.infotech, self.sp2009, True)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='chair1committee', acquired=True).count(),
            1)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='chair2committees',
            acquired=False).count(), 1)

    def test_2_different_chair_semesters(self):
        # being chair of 2 different cmmitteees gives chair2committees
        self.create_officer(self.sample_user, self.historian, self.sp2009,
                            True)
        self.create_officer(self.sample_user, self.infotech, self.fa2009, True)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='chair2committees',
            acquired=True).count(), 1)

    def test_twice_chair_of_same_committee(self):
        # being chair of the same committee twice doesn't give chair2committees
        self.create_officer(self.sample_user, self.infotech, self.fa2009, True)
        self.create_officer(self.sample_user, self.infotech, self.sp2010, True)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='chair2committees',
            acquired=True).count(), 0)

    def test_three_diff_positions(self):
        # having three different officer positions confers the achievement
        self.create_officer(self.sample_user, self.infotech, self.fa2009)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='three_unique_positions',
            acquired=True).count(), 0)

        self.create_officer(self.sample_user, self.historian, self.sp2010)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='three_unique_positions',
            acquired=True).count(), 0)

        self.create_officer(self.sample_user, self.vicepres, self.fa2010)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='three_unique_positions',
            acquired=True).count(), 1)

    def test_three_same_positions(self):
        # having some repeats within the 3 does not confer achievement
        self.create_officer(self.sample_user, self.infotech, self.fa2009)
        self.create_officer(self.sample_user, self.infotech, self.sp2010)
        self.create_officer(self.sample_user, self.vicepres, self.fa2010)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='three_unique_positions',
            acquired=True).count(), 0)

        self.create_officer(self.sample_user, self.vicepres, self.sp2011)
        self.create_officer(self.sample_user, self.infotech, self.fa2011)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='three_unique_positions',
            acquired=True).count(), 0)

        self.create_officer(self.sample_user, self.historian, self.sp2012)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='three_unique_positions',
            acquired=True).count(), 1)

    def test_two_and_three_in_a_row(self):
        # being the same position 3x in a row confers both achievements
        self.create_officer(self.sample_user, self.infotech, self.sp2009)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='twice_same_position',
            acquired=True).count(), 0)

        self.create_officer(self.sample_user, self.infotech, self.fa2009)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='twice_same_position',
            acquired=True).count(), 1)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='thrice_same_position',
            acquired=True).count(), 0)

        self.create_officer(self.sample_user, self.infotech, self.sp2010)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='thrice_same_position',
            acquired=True).count(), 1)

    def test_broken_streaks(self):
        # an officer being the same position thrice but not in a row does
        # not confer the achievement
        self.create_officer(self.sample_user, self.infotech, self.sp2009)
        self.create_officer(self.sample_user, self.historian, self.fa2009)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='twice_same_position',
            acquired=True).count(), 0)

        self.create_officer(self.sample_user, self.infotech, self.sp2010)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='twice_same_position',
            acquired=True).count(), 0)

        self.create_officer(self.sample_user, self.infotech, self.fa2010)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='twice_same_position',
            acquired=True).count(), 1)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='thrice_same_position',
            acquired=True).count(), 0)

    def test_multiple_streaks(self):
        # an officer being two positions each twice in a row gets it
        self.create_officer(self.sample_user, self.infotech, self.sp2009)
        self.create_officer(self.sample_user, self.infotech, self.fa2009)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='two_repeated_positions',
            acquired=True).count(), 0)

        self.create_officer(self.sample_user, self.historian, self.sp2010)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='two_repeated_positions',
            acquired=True).count(), 0)

        self.create_officer(self.sample_user, self.historian, self.fa2010)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='two_repeated_positions',
            acquired=True).count(), 1)

    def test_same_committee_two_different_streaks(self):
        # two repeated positions need to be different positions
        self.create_officer(self.sample_user, self.infotech, self.sp2009)
        self.create_officer(self.sample_user, self.infotech, self.fa2009)
        self.create_officer(self.sample_user, self.historian, self.sp2010)
        self.create_officer(self.sample_user, self.infotech, self.fa2010)
        self.create_officer(self.sample_user, self.infotech, self.sp2011)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='two_repeated_positions',
            acquired=True).count(), 0)

    def test_straight_to_the_top_vp(self):
        # becoming vp in 2 semesters gives this achievement
        self.create_officer(self.sample_user, self.historian, self.sp2009)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='straighttothetop',
            acquired=True).count(), 0)

        self.create_officer(self.sample_user, self.vicepres, self.fa2009)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='straighttothetop',
            acquired=True).count(), 1)

    def test_straight_to_the_top_pres(self):
        # becoming pres in 3 semesters also gives this achievement
        self.create_officer(self.sample_user, self.historian, self.sp2009)
        self.create_officer(self.sample_user, self.historian, self.fa2009)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='straighttothetop',
            acquired=True).count(), 0)

        self.create_officer(self.sample_user, self.president, self.sp2010)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='straighttothetop',
            acquired=True).count(), 1)

    def test_late_to_the_top(self):
        # becoming vp after 2 semesters or pres after 3 does not give it
        self.create_officer(self.sample_user, self.historian, self.sp2009)
        self.create_officer(self.sample_user, self.historian, self.fa2009)
        self.create_officer(self.sample_user, self.vicepres, self.sp2010)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='straighttothetop',
            acquired=True).count(), 0)

        self.create_officer(self.sample_user, self.president, self.fa2010)
        self.assertEqual(self.achievements.filter(
            achievement__short_name='straighttothetop',
            acquired=True).count(), 0)
