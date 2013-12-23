import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
import mox

from quark.base.models import OfficerPosition
from quark.base.models import Term
from quark.project_reports.models import ProjectReport


class ProjectReportTest(TestCase):
    fixtures = ['officer_position.yaml']

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='user',
            email='user@tbp.berkeley.edu',
            password='pwpwpwpwpw',
            first_name='Bentley',
            last_name='Bent')

        self.committee = OfficerPosition.objects.get(short_name='it')

        self.term = Term(term=Term.SPRING, year=2012, current=True)
        self.term.save()

        self.project_report = ProjectReport(
            term=self.term,
            author=self.user,
            committee=self.committee,
            title='Test',
            date=timezone.now().date())
        self.project_report.save()

        self.mox = mox.Mox()
        self.tz = timezone.get_current_timezone()

    def tearDown(self):
        self.mox.UnsetStubs()

    def test_completed_time(self):
        self.mox.StubOutWithMock(timezone, 'now')

        mock_time = timezone.make_aware(
            datetime.datetime(2012, 01, 01, 01, 01, 01), self.tz)
        timezone.now().MultipleTimes().AndReturn(mock_time)

        self.mox.ReplayAll()

        self.assertFalse(self.project_report.complete)
        self.assertIsNone(self.project_report.first_completed_at)

        self.project_report.complete = True
        self.project_report.save()

        self.assertEquals(self.project_report.first_completed_at, mock_time)
        self.assertTrue(self.project_report.complete)

        # Make sure that we can unset the completed_at date if it's no longer
        # complete.
        self.project_report.complete = False
        self.project_report.save()
        self.assertFalse(self.project_report.complete)
        self.assertIsNone(self.project_report.first_completed_at)

        self.mox.VerifyAll()

    def test_complete_time_no_overwrite(self):
        original_time = timezone.make_aware(
            datetime.datetime(2012, 01, 01, 01, 01, 01), self.tz)

        self.project_report.complete = True
        self.project_report.first_completed_at = original_time
        self.project_report.save()

        # Make sure that a save doesn't change anything if there is already a
        # time recorded.
        self.assertEquals(self.project_report.first_completed_at,
                          original_time)
        self.assertTrue(self.project_report.complete)

    def test_word_count(self):
        self.project_report.description = 'one two'
        self.project_report.purpose = 'three four'
        self.project_report.organization = 'five six'
        self.project_report.cost = 'seven eight'
        self.project_report.problems = 'nine'
        self.project_report.results = 'ten'

        self.assertEquals(self.project_report.word_count(), 10)
