from django.test import TestCase

from quark.pie_match.models import Alliance


class AllianceTest(TestCase):
    def test_get_total_score(self):
        alliance = Alliance()
        alliance.autonomous = 1
        alliance.manual = 2
        alliance.bonus = 3
        alliance.penalty = 4
        self.assertEquals(2, alliance.get_total_score())
