import os
import shutil

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.conf import settings
from django.core.files import File
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone

from quark.base.models import Officer
from quark.base.models import OfficerPosition
from quark.base.models import Term
from quark.candidates.models import Candidate
from quark.candidates.models import CandidateRequirement
from quark.candidates.models import CandidateRequirementProgress
from quark.candidates.models import Challenge
from quark.candidates.models import ChallengeCandidateRequirement
from quark.candidates.models import ChallengeType
from quark.candidates.models import EventCandidateRequirement
from quark.candidates.models import ExamFileCandidateRequirement
from quark.candidates.models import ManualCandidateRequirement
from quark.courses.models import CourseInstance
from quark.events.models import Event
from quark.events.models import EventAttendance
from quark.events.models import EventType
from quark.exams.models import Exam
from quark.shortcuts import get_object_or_none
from quark.user_profiles.models import StudentOrgUserProfile


@override_settings(
    MEDIA_ROOT=os.path.join(settings.WORKSPACE_ROOT, 'media', 'tests'))
class CandidateTest(TestCase):
    fixtures = ['test/course_instance.yaml']

    def setUp(self):
        self.candidate_group = Group.objects.create(name='Current Candidate')
        self.member_group = Group.objects.create(name='Member')

        user_model = get_user_model()
        # Create candidate
        self.user = user_model.objects.create_user(
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
        officer_user = user_model.objects.create_user(
            username='officer',
            email='it@tbp.berkeley.edu',
            password='password',
            first_name='Joe',
            last_name='Officer')
        committee = OfficerPosition(
            short_name='IT_test',
            long_name='Information Technology (test)',
            rank=2,
            mailing_list='IT')
        committee.save()
        self.officer = Officer(user=officer_user, position=committee,
                               term=self.term, is_chair=False)
        self.officer.save()

        # Create some manual candidate requirements
        self.manual_req1 = ManualCandidateRequirement(
            name='Manual 1',
            requirement_type=CandidateRequirement.MANUAL,
            credits_needed=2,
            term=self.term)
        self.manual_req1.save()
        self.manual_req2 = ManualCandidateRequirement(
            name='Manual 2',
            requirement_type=CandidateRequirement.MANUAL,
            credits_needed=5,
            term=self.term)
        self.manual_req2.save()

        # Create a challenge type
        self.individual_challenge_type = ChallengeType(name='Individual')
        self.individual_challenge_type.save()

        # Create a challenge requirement
        self.challenge_req = ChallengeCandidateRequirement(
            challenge_type=self.individual_challenge_type,
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
                                contact=officer_user,
                                committee=committee)
        self.fun_event1.save()
        self.fun_event2 = Event(name='Big Fun Event',
                                event_type=self.event_type1,
                                start_datetime=timezone.now(),
                                end_datetime=timezone.now(),
                                requirements_credit=2,
                                term=self.term,
                                location='A test location',
                                contact=officer_user,
                                committee=committee)
        self.fun_event2.save()
        self.notfun_event = Event(name='Not Fun Event',
                                  event_type=self.event_type2,
                                  start_datetime=timezone.now(),
                                  end_datetime=timezone.now(),
                                  term=self.term,
                                  location='A test location',
                                  contact=officer_user,
                                  committee=committee)
        self.notfun_event.save()
        self.event_req = EventCandidateRequirement(
            event_type=self.event_type1,
            credits_needed=4,
            term=self.term)
        self.event_req.save()

        # Create some exam files and exam files requirement
        test_file = open('test.txt', 'w+')
        test_file.write('This is a test file.')
        self.test_exam1 = Exam(
            course_instance=CourseInstance.objects.get(pk=10000),
            exam_number=Exam.MT1,
            exam_type=Exam.EXAM, verified=True, exam_file=File(test_file))
        self.test_exam1.save()
        self.test_exam1.course_instance.course.department.save()
        self.test_exam2 = Exam(
            course_instance=CourseInstance.objects.get(pk=20000),
            exam_number=Exam.MT1,
            exam_type=Exam.EXAM, verified=True, exam_file=File(test_file))
        self.test_exam2.save()
        self.test_exam2.course_instance.course.department.save()
        self.exam_req = ExamFileCandidateRequirement(
            credits_needed=2,
            term=self.term)
        self.exam_req.save()

    @classmethod
    def tearDownClass(cls):
        os.remove('test.txt')
        shutil.rmtree(os.path.join(settings.WORKSPACE_ROOT, 'media', 'tests'),
                      ignore_errors=True)

    def test_candidate_post_save(self):
        student_org_profile = get_object_or_none(
            StudentOrgUserProfile, user=self.user)

        # Candidate has already been saved for this user created above, so
        # StudentOrgUserProfile should exist:
        self.assertIsNotNone(student_org_profile)

        # Candidate has not been marked as initiated, so initiation_term should
        # be None in their profile, and the candidate should be in the Current
        # Candidate group and not in the Member group:
        self.assertIsNone(student_org_profile.initiation_term)
        candidate_groups = self.candidate.user.groups.all()
        self.assertIn(self.candidate_group, candidate_groups)
        self.assertNotIn(self.member_group, candidate_groups)

        # Mark candidate as initiated, so profile and groups should update to
        # match:
        self.candidate.initiated = True
        self.candidate.save()
        student_org_profile = get_object_or_none(
            StudentOrgUserProfile, user=self.user)
        self.assertEqual(student_org_profile.initiation_term, self.term)
        candidate_groups = self.candidate.user.groups.all()
        self.assertNotIn(self.candidate_group, candidate_groups)
        self.assertIn(self.member_group, candidate_groups)

    def test_manual_requirements(self):
        """Test that credits for manual requirements are counted correctly."""
        # Create some candidate progress
        CandidateRequirementProgress(
            candidate=self.candidate,
            requirement=self.manual_req1,
            manually_recorded_credits=2,
            alternate_credits_needed=2).save()
        progress = self.candidate.get_progress(CandidateRequirement.MANUAL)
        self.assertEqual(progress['completed'], 2)
        self.assertEqual(progress['required'], 7)

        # Test the simple summing of credits
        progress2 = CandidateRequirementProgress(
            candidate=self.candidate,
            requirement=self.manual_req2,
            manually_recorded_credits=3,
            alternate_credits_needed=5)
        progress2.save()
        progress = self.candidate.get_progress(CandidateRequirement.MANUAL)
        self.assertEqual(progress['completed'], 5)
        self.assertEqual(progress['required'], 7)

        # Test alternate credit requirement
        progress2.alternate_credits_needed = 4
        progress2.save()
        progress = self.candidate.get_progress(CandidateRequirement.MANUAL)
        self.assertEqual(progress['completed'], 5)
        self.assertEqual(progress['required'], 6)

    def test_challenge_requirements(self):
        """Test that credits for challenges are counted correctly."""
        # Make sure unverified challenges don't count
        challenge = Challenge(
            candidate=self.candidate,
            description='Hello kitty',
            verifying_user=self.officer.user,
            challenge_type=self.individual_challenge_type)
        challenge.save()
        progress = self.candidate.get_progress(CandidateRequirement.CHALLENGE)
        self.assertEqual(progress['completed'], 0)
        self.assertEqual(progress['required'], 3)

        # ...and verified challenges do count
        challenge.verified = True
        challenge.save()
        progress = self.candidate.get_progress(CandidateRequirement.CHALLENGE)
        self.assertEqual(progress['completed'], 1)
        self.assertEqual(progress['required'], 3)

        # Test alternate credit requirement
        CandidateRequirementProgress(
            candidate=self.candidate,
            requirement=self.challenge_req,
            alternate_credits_needed=2).save()
        progress = self.candidate.get_progress(CandidateRequirement.CHALLENGE)
        self.assertEqual(progress['completed'], 1)
        self.assertEqual(progress['required'], 2)

    def test_event_requirements(self):
        """Test that credits for events are counted correctly based on
        attendance.
        """
        # Attend Fun Event
        EventAttendance(event=self.fun_event1, user=self.user).save()
        progress = self.candidate.get_progress(CandidateRequirement.EVENT)
        self.assertEqual(progress['completed'], 1)

        # Attend Big Fun Event (worth 2)
        EventAttendance(event=self.fun_event2, user=self.user).save()
        progress = self.candidate.get_progress(CandidateRequirement.EVENT)
        self.assertEqual(progress['completed'], 3)

        # Attend Not Fun Event (not worth any requirements)
        EventAttendance(event=self.notfun_event, user=self.user).save()
        progress = self.candidate.get_progress(CandidateRequirement.EVENT)
        self.assertEqual(progress['completed'], 3)

    def test_exams_requirements(self):
        """Test that credits for exam files are counted correctly."""
        # Upload 1 verified exam
        self.test_exam1.submitter = self.user
        self.test_exam1.save()
        self.assertEqual(self.user, self.test_exam1.submitter)
        progress = self.candidate.get_progress(CandidateRequirement.EXAM_FILE)
        self.assertEqual(progress['completed'], 1)

        # Upload 2 verified exams
        self.test_exam2.submitter = self.user
        self.test_exam2.save()
        progress = self.candidate.get_progress(CandidateRequirement.EXAM_FILE)
        self.assertEqual(progress['completed'], 2)

        # Unverify an exam (doesn't count anymore)
        self.test_exam1.verified = False
        self.test_exam1.save()
        progress = self.candidate.get_progress(CandidateRequirement.EXAM_FILE)
        self.assertEqual(progress['completed'], 1)

    def test_get_total_progress(self):
        """Test get_progress where requirement_type is not specified and
        total progress for all requirements is returned.
        """
        # Get all the requirements that were created:
        requirements = CandidateRequirement.objects.filter(term=self.term)
        num_required = 0
        for requirement in requirements:
            num_required += requirement.credits_needed
        progress = self.candidate.get_progress()

        # Ensure that the method returns the same value as calculated manually.
        # This value should not change over the course of the tests.
        self.assertEqual(progress['required'], num_required)

        # Haven't assigned any completions yet:
        total_completed = 0
        self.assertEqual(progress['completed'], total_completed)

        # Attend Fun Event for fun event requirement
        EventAttendance(event=self.fun_event1, user=self.user).save()
        progress = self.candidate.get_progress()
        self.assertEqual(progress['required'], num_required)
        total_completed += 1
        self.assertEqual(progress['completed'], total_completed)

        # Complete a challenge:
        Challenge(candidate=self.candidate, description='Hello kitty',
                  verifying_user=self.officer.user,
                  verified=True,
                  challenge_type=self.individual_challenge_type).save()
        progress = self.candidate.get_progress()
        total_completed += 1
        self.assertEqual(progress['required'], num_required)
        self.assertEqual(progress['completed'], total_completed)

        # Attend an event not worth any requirements
        EventAttendance(event=self.notfun_event, user=self.user).save()
        progress = self.candidate.get_progress()
        self.assertEqual(progress['required'], num_required)
        self.assertEqual(progress['completed'], total_completed)


class CandidateViewsTest(TestCase):
    fixtures = ['major.yaml', 'groups.yaml', 'university.yaml',
                'test/term.yaml']

    def setUp(self):
        self.superuser = get_user_model().objects.create_user(
            username='superuser', email='it@tbp.berkeley.edu',
            password='password')
        self.superuser.is_superuser = True
        self.superuser.save()

    def test_candidate_create_view(self):
        post_data = {'username': 'candidate', 'email': 'email1@example.com',
                     'alt_email': 'email2@example.com',
                     'password1': 'password', 'password2': 'password',
                     'first_name': 'Random', 'preferred_name': 'Joe',
                     'middle_name': 'Luser', 'last_name': 'Candidate',
                     'birthday_year': '1995', 'birthday_month': '1',
                     'birthday_day': '1', 'gender': 'F',
                     'major': ('1000', '1001'), 'start_term': '20114',
                     'grad_term': '20144', 'cell_phone': '123-456-7890',
                     'receive_text': 'on', 'local_address1': '1 TBP Road',
                     'local_city': 'Location', 'local_state': 'AL',
                     'local_zip': '12345',
                     'international_address': 'Olympus Mons, Mars'}
        view_url = reverse('candidates:create')
        success_url = reverse('candidates:list')

        # Check that we can load the page
        self.assertTrue(self.client.login(
            username='superuser', password='password'))
        response = self.client.get(view_url)
        self.assertEqual(response.status_code, 200)

        # Post the data and check that we are redirected to the success URL
        response = self.client.post(view_url, post_data)
        self.assertRedirects(response, success_url)

        # Check that the candidate was created correctly
        cand = Candidate.objects.get(user__username='candidate')
        self.assertTrue(cand.user.userprofile)
        self.assertEqual(cand.term, Term.objects.get_current_term())

        self.assertEqual(cand.user.email, post_data['email'])
        self.assertEqual(cand.user.userprofile.alt_email,
                         post_data['alt_email'])
        self.assertEqual(cand.user.first_name, post_data['first_name'])
        self.assertEqual(cand.user.userprofile.preferred_name,
                         post_data['preferred_name'])
        self.assertEqual(cand.user.userprofile.middle_name,
                         post_data['middle_name'])
        self.assertEqual(cand.user.last_name, post_data['last_name'])
        self.assertEqual(str(cand.user.userprofile.birthday), '1995-01-01')

        for major_id in post_data['major']:
            self.assertTrue(cand.user.collegestudentinfo.major.get(
                id=int(major_id)))
        self.assertEqual(cand.user.collegestudentinfo.start_term.id,
                         int(post_data['start_term']))
        self.assertEqual(cand.user.collegestudentinfo.grad_term.id,
                         int(post_data['grad_term']))

        self.assertEqual(cand.user.userprofile.cell_phone,
                         post_data['cell_phone'])
        self.assertTrue(cand.user.userprofile.receive_text)
        self.assertEqual(cand.user.userprofile.local_address1,
                         post_data['local_address1'])
        self.assertEqual(cand.user.userprofile.local_city,
                         post_data['local_city'])
        self.assertEqual(cand.user.userprofile.local_state,
                         post_data['local_state'])
        self.assertEqual(cand.user.userprofile.local_zip,
                         post_data['local_zip'])
        self.assertEqual(cand.user.userprofile.international_address,
                         post_data['international_address'])
