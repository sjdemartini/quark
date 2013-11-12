from django.contrib.auth import get_user_model
from django.test import TestCase

from quark.base.models import Term
from quark.base_tbp.models import Officer
from quark.base_tbp.models import OfficerPosition


class OfficerPositionTest(TestCase):
    fixtures = ['officer_position.yaml']

    def test_save(self):
        num = OfficerPosition.objects.count()
        tbp_officer = OfficerPosition(
            position_type=OfficerPosition.TBP_OFFICER,
            short_name='IT_test',
            long_name='Information Technology (test)',
            rank=2,
            mailing_list='IT')
        tbp_officer.save()

        self.assertTrue(
            OfficerPosition.objects.filter(
                position_type=OfficerPosition.TBP_OFFICER).exists())
        pie_coord = OfficerPosition(
            position_type=OfficerPosition.TBP_OFFICER,
            short_name='PiE Coord test',
            long_name='PiE Coordinator (test)',
            rank=3,
            mailing_list='PiE')
        pie_coord.save()

        positions = OfficerPosition.objects.order_by('pk')
        self.assertEquals(len(positions) - num, 2)
        self.assertEquals(positions[num].short_name, 'IT_test')
        self.assertEquals(positions[num].rank, 2)
        self.assertEquals(positions[num + 1].short_name, 'PiE Coord test')
        self.assertEquals(positions[num + 1].rank, 3)

    def test_base_initial_data(self):
        """
        Basic test to verify that the initial data put in the
        initial_data.json file are correctly formatted and
        the number that appear in the database is as expected.
        """
        num = len(OfficerPosition.objects.filter(
            position_type=OfficerPosition.TBP_OFFICER))
        self.assertEquals(num, 22)


class OfficerTest(TestCase):
    fixtures = ['officer_position.yaml']

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='officer',
            email='it@tbp.berkeley.edu',
            password='officerpw',
            first_name='Off',
            last_name='Icer')
        self.term = Term(term=Term.SPRING, year=2012, current=True)
        self.term.save()
        self.position = OfficerPosition(
            position_type=OfficerPosition.TBP_OFFICER,
            short_name='IT_test',
            long_name='Information Technology (test)',
            rank=2,
            mailing_list='IT')
        self.position.save()

    def test_save(self):
        it_chair = Officer(user=self.user, position=self.position,
                           term=self.term, is_chair=True)
        it_chair.save()

        self.assertTrue(Officer.objects.filter(is_chair=True).exists())

        new_term = Term(term=Term.FALL, year=2011, current=False)
        new_term.save()
        it_officer = Officer(user=self.user, position=self.position,
                             term=new_term, is_chair=False)
        it_officer.save()
        officers = Officer.objects.filter(is_chair=True)

        self.assertEquals(len(officers), 1)
        self.assertEquals(officers[0].user, self.user)
