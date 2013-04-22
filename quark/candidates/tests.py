import os
import shutil

from django.conf import settings
from django.core.files import File
from django.test import TestCase
from django.utils import timezone

from quark.auth.models import User
from quark.base.models import Term
from quark.base_tbp.models import Officer
from quark.base_tbp.models import OfficerPosition
from quark.candidates.models import Candidate
from quark.candidates.models import CandidateRequirement
from quark.candidates.models import CandidateProgress
from quark.candidates.models import Challenge
from quark.candidates.models import ChallengeCandidateRequirement
from quark.candidates.models import EventCandidateRequirement
from quark.candidates.models import ExamFileCandidateRequirement
from quark.courses.models import CourseInstance
from quark.events.models import Event
from quark.events.models import EventAttendance
from quark.events.models import EventType
from quark.exam_files.models import Exam
from quark.shortcuts import get_object_or_none
from quark.user_profiles.models import TBPProfile


class CandidateTest(TestCase):
    fixtures = ['test/course_instance.yaml']

    def setUp(self):
        # Create candidate
        self.user = User.objects.create_user(
            username='luser',
            email='test@tbp.berkeley.edu',
            password='password',
            first_name='Random',
            last_name='Candidate')
        self.term = Term(term=Term.SPRING, year=2012, current=True)
        self.term.save()
        self.candidate = Candidate(user=self.user, term=self.term)
        self.candidate.save()

        # Create officer
        officer_user = User.objects.create_user(
            username='officer',
            email='it@tbp.berkeley.edu',
            password='password',
            first_name='Joe',
            last_name='Officer')
        committee = OfficerPosition(
            position_type=OfficerPosition.TBP_OFFICER,
            short_name='IT_test',
            long_name='Information Technology (test)',
            rank=2,
            mailing_list='IT')
        committee.save()
        self.officer = Officer(user=officer_user, position=committee,
                               term=self.term, is_chair=False)
        self.officer.save()

        # Create some manual candidate requirements
        self.manual_req1 = CandidateRequirement(
            name='Manual 1',
            requirement_type=CandidateRequirement.MANUAL,
            credits_needed=2,
            term=self.term)
        self.manual_req1.save()
        self.manual_req2 = CandidateRequirement(
            name='Manual 2',
            requirement_type=CandidateRequirement.MANUAL,
            credits_needed=5,
            term=self.term)
        self.manual_req2.save()

        # Create a challenge requirement
        self.challenge_req = ChallengeCandidateRequirement(
            name='Challenge',
            challenge_type=Challenge.INDIVIDUAL,
            credits_needed=3,
            term=self.term)
        self.challenge_req.save()

        # Create some events and event requirement
        self.event_type1 = EventType(name='Fun')
        self.event_type1.save()
        self.event_type2 = EventType(name='Not Fun')
        self.event_type2.save()
        self.fun_event1 = Event(name='Fun Event',
                                event_type=self.event_type1,
                                start_datetime=timezone.now(),
                                end_datetime=timezone.now(),
                                term=self.term,
                                location='A test location',
                                contact=officer_user)
        self.fun_event1.save()
        self.fun_event2 = Event(name='Big Fun Event',
                                event_type=self.event_type1,
                                start_datetime=timezone.now(),
                                end_datetime=timezone.now(),
                                requirements_credit=2,
                                term=self.term,
                                location='A test location',
                                contact=officer_user)
        self.fun_event2.save()
        self.notfun_event = Event(name='Not Fun Event',
                                  event_type=self.event_type2,
                                  start_datetime=timezone.now(),
                                  end_datetime=timezone.now(),
                                  term=self.term,
                                  location='A test location',
                                  contact=officer_user)
        self.notfun_event.save()
        self.event_req = EventCandidateRequirement(
            name='Mandatory Fun',
            event_type=self.event_type1,
            credits_needed=4,
            term=self.term)
        self.event_req.save()

        # Create some exam files and exam files requirement
        test_file = open('test.txt', 'w+')
        test_file.write('This is a test file.')
        self.test_exam1 = Exam(
            course_instance=CourseInstance.objects.get(pk=10000),
            exam=Exam.MT1,
            exam_type=Exam.EXAM, approved=True, exam_file=File(test_file))
        self.test_exam1.save()
        self.test_exam1.course_instance.course.department.save()
        self.folder1 = self.test_exam1.unique_id[0:2]
        self.test_exam2 = Exam(
            course_instance=CourseInstance.objects.get(pk=20000),
            exam=Exam.MT1,
            exam_type=Exam.EXAM, approved=True, exam_file=File(test_file))
        self.test_exam2.save()
        self.test_exam2.course_instance.course.department.save()
        self.folder2 = self.test_exam2.unique_id[0:2]
        self.exam_req = ExamFileCandidateRequirement(
            name='Exam files',
            credits_needed=2,
            term=self.term)
        self.exam_req.save()

    def tearDown(self):
        folder1 = os.path.join(
            settings.MEDIA_ROOT, Exam.EXAM_FILES_LOCATION, self.folder1)
        folder2 = os.path.join(
            settings.MEDIA_ROOT, Exam.EXAM_FILES_LOCATION, self.folder2)
        shutil.rmtree(folder1)
        shutil.rmtree(folder2)
        os.remove('test.txt')

    def test_candidate_post_save(self):
        tbp_profile = get_object_or_none(TBPProfile, user=self.user)

        # Candidate has already been saved for this user created above, so
        # TBPProfile should exist:
        self.assertIsNotNone(tbp_profile)

        # Candidate has not been marked as initiated, so initiation_term should
        # be None in their profile:
        self.assertIsNone(tbp_profile.initiation_term)

        # Mark candidate as initiated, and profile should update to match:
        self.candidate.initiated = True
        self.candidate.save()
        tbp_profile = get_object_or_none(TBPProfile, user=self.user)
        self.assertEqual(tbp_profile.initiation_term, self.term)

    def test_manual_requirements(self):
        """
        Test that credits for manual requirements are counted correctly.
        """
        # Create some candidate progress
        CandidateProgress(
            candidate=self.candidate,
            requirement=self.manual_req1,
            credits_earned=2).save()
        complete, needed = self.candidate.get_progress(
            CandidateRequirement.MANUAL)
        self.assertEqual(complete, 2)
        self.assertEqual(needed, 7)

        # Test the simple summing of credits
        progress2 = CandidateProgress(
            candidate=self.candidate,
            requirement=self.manual_req2,
            credits_earned=3)
        progress2.save()
        complete, needed = self.candidate.get_progress(
            CandidateRequirement.MANUAL)
        self.assertEqual(complete, 5)
        self.assertEqual(needed, 7)

        # Test credits exempted
        progress2.credits_exempted = 1
        progress2.save()
        complete, needed = self.candidate.get_progress(
            CandidateRequirement.MANUAL)
        self.assertEqual(complete, 5)
        self.assertEqual(needed, 6)

    def test_challenge_requirements(self):
        """
        Test that credits for challenges are counted correctly.
        """
        # Make sure unverified challenges don't count
        challenge = Challenge(
            candidate=self.candidate,
            description='Hello kitty',
            officer=self.officer)
        challenge.save()
        complete, needed = self.candidate.get_progress(
            CandidateRequirement.CHALLENGE)
        self.assertEqual(complete, 0)
        self.assertEqual(needed, 3)

        # ...and verified challenges do count
        challenge.verified = True
        challenge.save()
        complete, _ = self.candidate.get_progress(
            CandidateRequirement.CHALLENGE)
        self.assertEqual(complete, 1)

        # Test exemptions
        CandidateProgress(
            candidate=self.candidate,
            requirement=self.challenge_req,
            credits_exempted=1).save()
        _, needed = self.candidate.get_progress(CandidateRequirement.CHALLENGE)
        self.assertEqual(needed, 2)

    def test_event_requirements(self):
        """
        Test that credits for events are counted correctly based on attendance.
        """
        # Attend Fun Event
        EventAttendance(event=self.fun_event1,
                        person=self.user).save()
        complete, _ = self.candidate.get_progress(CandidateRequirement.EVENT)
        self.assertEqual(complete, 1)

        # Attend Big Fun Event (worth 2)
        EventAttendance(event=self.fun_event2,
                        person=self.user).save()
        complete, _ = self.candidate.get_progress(CandidateRequirement.EVENT)
        self.assertEqual(complete, 3)

        # Attend Not Fun Event (not worth any requirements)
        EventAttendance(event=self.notfun_event,
                        person=self.user).save()
        complete, _ = self.candidate.get_progress(CandidateRequirement.EVENT)
        self.assertEqual(complete, 3)

    def test_exam_files_requirements(self):
        """
        Test that credits for exam files are counted correctly.
        """
        # Upload 1 approved exam
        self.test_exam1.submitter = self.user
        self.test_exam1.save()
        complete, _ = self.candidate.get_progress(
            CandidateRequirement.EXAM_FILE)
        self.assertEqual(self.user, self.test_exam1.submitter)
        self.assertEqual(complete, 1)

        # Upload 2 approved exams
        self.test_exam2.submitter = self.user
        self.test_exam2.save()
        complete, _ = self.candidate.get_progress(
            CandidateRequirement.EXAM_FILE)
        self.assertEqual(complete, 2)

        # Unapprove an exam (doesn't count anymore)
        self.test_exam1.approved = False
        self.test_exam1.save()
        complete, _ = self.candidate.get_progress(
            CandidateRequirement.EXAM_FILE)
        self.assertEqual(complete, 1)
