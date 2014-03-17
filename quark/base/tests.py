from test.test_support import EnvironmentVarGuard
from test.test_support import import_fresh_module

from django import forms
from django.contrib.auth.models import AnonymousUser
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.template import Context
from django.template import Template
from django.test import TestCase
from django.test.utils import override_settings

from quark.base import fields
from quark.base.models import Major
from quark.base.models import Officer
from quark.base.models import OfficerPosition
from quark.base.models import Term
from quark.base.models import University
from quark.settings.dev import DATABASES as DEV_DB
from quark.settings.production import DATABASES as PROD_DB
from quark.settings.staging import DATABASES as STAGING_DB


class MajorTest(TestCase):
    fixtures = ['major.yaml', 'university.yaml']

    def test_initial_number(self):
        num = Major.objects.count()
        self.assertEqual(num, 15)

    def test_uniqueness(self):
        ucb = University.objects.get(short_name='UCB')
        duplicate = Major(
            short_name='math',
            long_name='Math',
            university=ucb,
            website='http://math.berkeley.edu')
        self.assertRaises(IntegrityError, duplicate.save)


class TermManagerTest(TestCase):
    def test_get_current_term(self):
        Term(term=Term.SPRING, year=2012, current=False).save()
        Term(term=Term.FALL, year=2012, current=True).save()
        term = Term.objects.get_current_term()
        self.assertEquals(term.term, Term.FALL)
        self.assertEquals(term.year, 2012)

    def test_get_current_term_undefined(self):
        Term(term=Term.SPRING, year=2012, current=False).save()
        Term(term=Term.FALL, year=2012, current=False).save()
        term = Term.objects.get_current_term()
        self.assertIsNone(term)

    def test_get_terms(self):
        # Intentionally unordered.
        Term(term=Term.FALL, year=2011, current=False).save()
        Term(term=Term.SUMMER, year=2012, current=True).save()
        Term(term=Term.SPRING, year=2012, current=False).save()
        Term(term=Term.SPRING, year=2011, current=False).save()

        terms = Term.objects.get_terms(include_summer=True)

        self.assertEquals(len(terms), 4)

        self.assertEquals(terms[0].year, 2011)
        self.assertEquals(terms[0].term, Term.SPRING)

        self.assertEquals(terms[1].year, 2011)
        self.assertEquals(terms[1].term, Term.FALL)

        self.assertEquals(terms[2].year, 2012)
        self.assertEquals(terms[2].term, Term.SPRING)

        self.assertEquals(terms[3].year, 2012)
        self.assertEquals(terms[3].term, Term.SUMMER)
        self.assertTrue(terms[3].current)

    def test_get_terms_reversed(self):
        # Intentionally unordered.
        Term(term=Term.FALL, year=2011, current=False).save()
        Term(term=Term.SUMMER, year=2012, current=True).save()
        Term(term=Term.SPRING, year=2012, current=False).save()
        Term(term=Term.SPRING, year=2011, current=False).save()

        terms = Term.objects.get_terms(
            include_summer=True, reverse=True)

        self.assertEquals(len(terms), 4)

        self.assertEquals(terms[0].year, 2012)
        self.assertEquals(terms[0].term, Term.SUMMER)
        self.assertTrue(terms[0].current)

        self.assertEquals(terms[1].year, 2012)
        self.assertEquals(terms[1].term, Term.SPRING)

        self.assertEquals(terms[2].year, 2011)
        self.assertEquals(terms[2].term, Term.FALL)

        self.assertEquals(terms[3].year, 2011)
        self.assertEquals(terms[3].term, Term.SPRING)

    def test_get_terms_no_summer(self):
        # Intentionally unordered.
        Term(term=Term.SUMMER, year=2012, current=True).save()
        Term(term=Term.FALL, year=2011, current=False).save()
        Term(term=Term.SPRING, year=2012, current=False).save()
        Term(term=Term.FALL, year=2012, current=False).save()

        terms = Term.objects.get_terms(
            include_future=True, include_summer=False)

        self.assertEquals(len(terms), 3)

        self.assertEquals(terms[0].year, 2011)
        self.assertEquals(terms[0].term, Term.FALL)

        self.assertEquals(terms[1].year, 2012)
        self.assertEquals(terms[1].term, Term.SPRING)

        self.assertEquals(terms[2].year, 2012)
        self.assertEquals(terms[2].term, Term.FALL)

    def test_get_terms_no_unknown(self):
        unknown = Term(term=Term.UNKNOWN, year=2011)
        unknown.save()
        spring = Term(term=Term.SPRING, year=2012)
        spring.save()
        fall = Term(term=Term.FALL, year=2013, current=True)
        fall.save()

        terms = Term.objects.get_terms(include_unknown=False)
        self.assertEquals(list(terms), [spring, fall])

        terms = Term.objects.get_terms(include_unknown=True)
        self.assertEquals(list(terms), [unknown, spring, fall])

    def test_get_terms_no_future(self):
        # Intentionally unordered.
        Term(term=Term.SUMMER, year=2012, current=False).save()
        Term(term=Term.FALL, year=2011, current=False).save()
        Term(term=Term.FALL, year=2012, current=False).save()
        Term(term=Term.SPRING, year=2012, current=True).save()

        terms = Term.objects.get_terms()

        self.assertEquals(len(terms), 2)

        self.assertEquals(terms[0].year, 2011)
        self.assertEquals(terms[0].term, Term.FALL)

        self.assertEquals(terms[1].year, 2012)
        self.assertEquals(terms[1].term, Term.SPRING)

    @override_settings(TERM_TYPE='quarter')
    def test_get_terms_quarter(self):
        # Intentionally unordered.
        Term(term=Term.WINTER, year=2012, current=True).save()

        terms = Term.objects.get_terms()

        self.assertEquals(len(terms), 1)

        self.assertEquals(terms[0].year, 2012)
        self.assertEquals(terms[0].term, Term.WINTER)

    @override_settings(TERM_TYPE='semester')
    def test_get_terms_semester(self):
        # Intentionally unordered.
        Term(term=Term.WINTER, year=2012, current=True).save()

        terms = Term.objects.get_terms()

        self.assertEquals(len(terms), 0)

    def test_get_terms_empty(self):
        terms = Term.objects.get_terms()
        self.assertEquals(len(terms), 0)

    def test_get_by_url_name(self):
        Term(term=Term.FALL, year=2012, current=True).save()
        term = Term.objects.get_by_url_name('fa2012')
        self.assertEquals(term.year, 2012)
        self.assertEquals(term.term, Term.FALL)
        self.assertTrue(term.current)

    def test_get_by_url_name_does_not_exist(self):
        term = Term.objects.get_by_url_name('fa2012')
        self.assertIsNone(term)

    def test_get_by_url_name_garbage(self):
        term = Term.objects.get_by_url_name('asdfasdf')
        self.assertIsNone(term)

    def test_get_by_url_name_empty(self):
        term = Term.objects.get_by_url_name('')
        self.assertIsNone(term)

    def test_get_by_url_name_not_string(self):
        term = Term.objects.get_by_url_name(5)
        self.assertIsNone(term)

    def test_get_by_natural_key(self):
        Term(term=Term.FALL, year=2012, current=True).save()
        term = Term.objects.get_by_natural_key(Term.FALL, 2012)
        self.assertEquals(term.year, 2012)
        self.assertEquals(term.term, Term.FALL)
        self.assertTrue(term.current)

    def test_get_by_natural_key_does_not_exist(self):
        term = Term.objects.get_by_natural_key(Term.FALL, 2012)
        self.assertIsNone(term)


class TermTest(TestCase):
    def test_save(self):
        spring = Term(term=Term.SPRING, year=2012, current=False)
        spring.save()
        fall = Term(term=Term.FALL, year=2012, current=False)
        fall.save()

        self.assertFalse(Term.objects.filter(current=True).exists())

        spring.current = True
        spring.save()
        current = Term.objects.filter(current=True)
        self.assertEquals(len(current), 1)
        self.assertEquals(current[0].year, 2012)
        self.assertEquals(current[0].term, Term.SPRING)

        fall.current = True
        fall.save()
        current = Term.objects.filter(current=True)
        self.assertEquals(len(current), 1)
        self.assertEquals(current[0].year, 2012)
        self.assertEquals(current[0].term, Term.FALL)

    def test_save_bad_pk(self):
        term = Term(term=Term.SPRING, year=2012, current=False)
        term.save()

        self.assertEquals(term.pk, 20122)
        self.assertEquals(term.year, 2012)
        self.assertEquals(term.term, Term.SPRING)

        term.year = 2013
        self.assertRaisesMessage(
            ValueError,
            ('You cannot update the year or term without '
             'also updating the primary key value.'),
            term.save)

        terms = Term.objects.all()
        self.assertEquals(len(terms), 1)
        term = terms[0]

        self.assertEquals(term.pk, 20122)
        self.assertEquals(term.year, 2012)
        self.assertEquals(term.term, Term.SPRING)

    def test_save_invalid_term(self):
        spring = Term(term=Term.UNKNOWN, year=0, current=True)
        spring.save()
        self.assertFalse(Term.objects.filter(current=True).exists())

    def test_unicode(self):
        term = Term(term=Term.FALL, year=2012, current=False)
        self.assertEqual(unicode(term), 'Fall 2012')

    def test_unicode_current(self):
        term = Term(term=Term.FALL, year=2012, current=True)
        self.assertEqual(unicode(term), 'Fall 2012 (Current)')

    def test_verbose_name(self):
        term = Term(term=Term.FALL, year=2012, current=False)
        self.assertEqual(term.verbose_name(), 'Fall 2012')

    def test_verbose_name_current(self):
        term = Term(term=Term.FALL, year=2012, current=True)
        self.assertEqual(term.verbose_name(), 'Fall 2012')

    def test_get_url_name(self):
        term = Term(term=Term.WINTER, year=2012, current=True)
        self.assertEqual(term.get_url_name(), 'wi2012')

        term = Term(term=Term.SPRING, year=2012, current=True)
        self.assertEqual(term.get_url_name(), 'sp2012')

        term = Term(term=Term.SUMMER, year=2012, current=True)
        self.assertEqual(term.get_url_name(), 'su2012')

        term = Term(term=Term.FALL, year=2012, current=True)
        self.assertEqual(term.get_url_name(), 'fa2012')

        term = Term(term=Term.UNKNOWN, year=2012, current=True)
        self.assertEqual(term.get_url_name(), 'un2012')

    def test_calculate_pk(self):
        term = Term(term=Term.WINTER, year=2012, current=True)
        self.assertEqual(term._calculate_pk(), 20121)

        term = Term(term=Term.SPRING, year=2012, current=True)
        self.assertEqual(term._calculate_pk(), 20122)

        term = Term(term=Term.SUMMER, year=2012, current=True)
        self.assertEqual(term._calculate_pk(), 20123)

        term = Term(term=Term.FALL, year=2012, current=True)
        self.assertEqual(term._calculate_pk(), 20124)

        term = Term(term=Term.UNKNOWN, year=2012, current=True)
        self.assertEqual(term._calculate_pk(), 20120)

    def test_comparisons(self):
        fall = Term(term=Term.FALL, year=2012)
        spring = Term(term=Term.SPRING, year=2012)
        self.assertTrue(spring < fall)
        self.assertTrue(spring <= fall)
        self.assertFalse(spring > fall)
        self.assertFalse(spring >= fall)
        self.assertTrue(fall <= fall)
        self.assertTrue(fall >= fall)

    def test_garbage_comparisons(self):
        term = Term(term=Term.FALL, year=1900)
        self.assertTrue(term < 'foo')
        self.assertTrue(term <= 'foo')
        self.assertFalse(term > 'foo')
        self.assertFalse(term >= 'foo')
        self.assertTrue(term != 'foo')
        self.assertFalse(term == 'foo')

    def test_equality(self):
        one = Term(term=Term.FALL, year=2012)
        two = Term(term=Term.FALL, year=2012)
        self.assertTrue(one == two)

    def test_inequality(self):
        spring = Term(term=Term.SPRING, year=2012)
        fall = Term(term=Term.FALL, year=2012)
        self.assertTrue(spring != fall)

    def test_natural_key(self):
        term = Term(term=Term.SPRING, year=2012)
        self.assertEqual(term.natural_key(), (Term.SPRING, 2012))


class UniversityTest(TestCase):
    fixtures = ['university.yaml']

    def test_initial_number(self):
        num = University.objects.count()
        self.assertEquals(num, 1)


class OfficerPositionTest(TestCase):
    fixtures = ['officer_position.yaml']

    def test_save(self):
        num = OfficerPosition.objects.count()
        it_officer = OfficerPosition(
            short_name='IT_test',
            long_name='Information Technology (test)',
            rank=2,
            mailing_list='IT')
        it_officer.save()

        self.assertTrue(OfficerPosition.objects.exists())
        exec_officer = OfficerPosition(
            short_name='exec test',
            long_name='Executive Officer (test)',
            rank=1,
            mailing_list='exec')
        exec_officer.save()

        positions = OfficerPosition.objects.order_by('pk')
        self.assertEquals(len(positions) - num, 2)
        self.assertEquals(positions[num].short_name, 'IT_test')
        self.assertEquals(positions[num].rank, 2)
        self.assertEquals(positions[num + 1].short_name, 'exec test')
        self.assertEquals(positions[num + 1].rank, 1)

    def test_base_initial_data(self):
        """
        Basic test to verify that the initial data put in the
        initial_data.json file are correctly formatted and
        the number that appear in the database is as expected.
        """
        num = OfficerPosition.objects.all().count()
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


class OfficerGroupsTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='officer',
            email='it@tbp.berkeley.edu',
            password='officerpw',
            first_name='Off',
            last_name='Icer')

        self.term = Term(term=Term.SPRING, year=2012, current=True)
        self.term.save()
        self.term_old = Term(term=Term.FALL, year=2011)
        self.term_old.save()

        self.position_exec = OfficerPosition(
            short_name='vp',
            long_name='Vice President',
            rank=1,
            mailing_list='vp',
            executive=True)
        self.position_exec.save()
        self.position_regular = OfficerPosition(
            short_name='it',
            long_name='Information Technology',
            rank=2,
            mailing_list='it')
        self.position_regular.save()
        self.position_auxiliary = OfficerPosition(
            short_name='advisor',
            long_name='Advisor',
            rank=3,
            mailing_list='advisor',
            auxiliary=True)
        self.position_auxiliary.save()

        # Some standard groups:
        self.officer_group = Group.objects.create(
            name='Officer')
        self.officer_group_curr = Group.objects.create(
            name='Current Officer')
        self.exec_group = Group.objects.create(
            name='Executive')
        self.exec_group_curr = Group.objects.create(
            name='Current Executive')

        # Groups from officer positions:
        self.pos_exec_group = Group.objects.create(
            name=self.position_exec.long_name)
        self.pos_exec_group_curr = Group.objects.create(
            name='Current {}'.format(self.position_exec.long_name))
        self.pos_reg_group = Group.objects.create(
            name=self.position_regular.long_name)
        self.pos_reg_group_curr = Group.objects.create(
            name='Current {}'.format(self.position_regular.long_name))
        self.pos_aux_group = Group.objects.create(
            name=self.position_auxiliary.long_name)
        self.pos_aux_group_curr = Group.objects.create(
            name='Current {}'.format(self.position_auxiliary.long_name))

    def test_get_corresponding_groups(self):
        """Test the OfficerPosition.get_corresponding_groups method."""
        # If we specify the term that is the current term, then the "Current"
        # groups should be included; otherwise, "Current" groups should not be
        # included.
        # Check the corresponding groups for a "regular" (non-auxiliary,
        # non-exec) officer position. We should expect the corresponding groups
        # to be Officer and the group specific to the position:
        groups = [self.officer_group, self.pos_reg_group]
        self.assertItemsEqual(
            groups,
            self.position_regular.get_corresponding_groups())
        self.assertItemsEqual(
            groups,
            self.position_regular.get_corresponding_groups(self.term_old))
        # For the current term:
        groups.extend([self.officer_group_curr, self.pos_reg_group_curr])
        self.assertItemsEqual(
            groups,
            self.position_regular.get_corresponding_groups(term=self.term))

        # For the executive position, the corresponding groups will also
        # include the "Executive" groups:
        groups = [self.officer_group, self.exec_group, self.pos_exec_group]
        self.assertItemsEqual(
            groups,
            self.position_exec.get_corresponding_groups())
        self.assertItemsEqual(
            groups,
            self.position_exec.get_corresponding_groups(self.term_old))
        # For the current term:
        groups.extend([self.officer_group_curr, self.exec_group_curr,
                       self.pos_exec_group_curr])
        self.assertItemsEqual(
            groups,
            self.position_exec.get_corresponding_groups(term=self.term))

        # For the auxiliary position, there should be no "Officer" group or
        # "Executive" group (since the position is non-exec):
        groups = [self.pos_aux_group]
        self.assertItemsEqual(
            groups,
            self.position_auxiliary.get_corresponding_groups())
        self.assertItemsEqual(
            groups,
            self.position_auxiliary.get_corresponding_groups(self.term_old))
        # For the current term:
        groups.append(self.pos_aux_group_curr)
        self.assertItemsEqual(
            groups,
            self.position_auxiliary.get_corresponding_groups(term=self.term))

    def test_add_groups(self):
        # Test the Officer method for adding the user to groups. Note that no
        # officer objects are saved, as that would activate post-saves, which
        # are tested seprately.
        officer = Officer(user=self.user, position=self.position_regular,
                          term=self.term)
        expected_groups = self.position_regular.get_corresponding_groups(
            term=self.term)
        self.assertFalse(self.user.groups.exists())
        officer._add_user_to_officer_groups()
        # Check that all of the expected groups were added for this user:
        self.assertTrue(self.user.groups.exists())
        for group in expected_groups:
            self.assertTrue(self.user.groups.filter(pk=group.pk).exists())

    def test_remove_groups(self):
        # Test the Officer method for removing the user from groups. Note that
        # unlike test_add_groups, this method saves the Officer objets, as the
        # _remove_user_from_officer_groups method depends on database entries
        # to work properly. Thus, this method relies on post-save functions for
        # adding groups for a user. (Post-saves are also tested separately.)
        self.assertFalse(self.user.groups.exists())  # No groups yet

        # Add a regular officer position (for which the post-save should add
        # groups):
        officer_reg = Officer(user=self.user, position=self.position_regular,
                              term=self.term)
        officer_reg.save()
        groups = list(self.user.groups.all())
        self.assertTrue(len(groups) > 0)

        # Add the groups for an exec officer position manually so that the
        # Officer object is not in the database (and does not need to be
        # deleted here before we can test the removal function), and the user's
        # group count should increase:
        officer_exec = Officer(user=self.user, position=self.position_exec,
                               term=self.term)
        officer_exec._add_user_to_officer_groups()
        self.assertTrue(len(groups) < self.user.groups.count())

        # Now remove groups from the exec position, and the user's groups
        # should return to the same positions as from before the exec position
        # added any:
        officer_exec._remove_user_from_officer_groups()
        self.assertItemsEqual(groups, list(self.user.groups.all()))

    def test_officer_post_save(self):
        """Test that a user is added to the appropriate groups on post-save."""
        self.assertFalse(self.user.groups.exists())  # No groups yet

        # Add a regular officer position (for which the post-save should add
        # groups):
        officer_reg = Officer(user=self.user, position=self.position_regular,
                              term=self.term)
        expected_groups = set(self.position_regular.get_corresponding_groups(
            term=self.term))
        self.assertFalse(self.user.groups.exists())
        officer_reg.save()
        # Check that all of the expected groups were added for this user:
        self.assertItemsEqual(expected_groups, self.user.groups.all())

        # Add another position, and check that the correct groups are added:
        officer_exec = Officer(user=self.user, position=self.position_exec,
                               term=self.term_old)
        officer_exec.save()
        expected_groups.update(self.position_exec.get_corresponding_groups(
            term=self.term_old))
        self.assertItemsEqual(expected_groups, self.user.groups.all())

    def test_officer_post_delete(self):
        """Test that a user is removed from the appropriate groups on
        post-delete.
        """
        self.assertFalse(self.user.groups.exists())  # No groups yet

        # Add a regular officer position (for which the post-save should add
        # groups):
        officer_reg = Officer(user=self.user, position=self.position_regular,
                              term=self.term)
        officer_reg.save()
        groups = list(self.user.groups.all())
        self.assertTrue(len(groups) > 0)

        # Add an exec officer position for this user, and the user's group
        # count should increase:
        officer_exec = Officer(user=self.user, position=self.position_exec,
                               term=self.term)
        officer_exec.save()
        self.assertTrue(len(groups) < self.user.groups.count())

        # Now delete exec officer, and the user's groups should return to the
        # same positions as from before the exec position added any:
        officer_exec.delete()
        self.assertItemsEqual(groups, list(self.user.groups.all()))

        # And delete the regular officer, and the user should be part of no
        # more groups:
        officer_reg.delete()
        self.assertFalse(self.user.groups.exists())

    def test_term_post_save(self):
        """Test that when terms are saved, the "Current" groups are kept
        up-to-date.
        """
        self.assertFalse(self.user.groups.exists())  # No groups yet

        # Add an exec officer position (for which the post-save should add
        # groups) in the current term:
        officer_exec = Officer(user=self.user, position=self.position_exec,
                               term=self.term)
        officer_exec.save()
        expected_groups = set(self.position_exec.get_corresponding_groups(
            term=self.term))
        groups = list(self.user.groups.all())
        self.assertTrue(len(groups) > 0)
        self.assertItemsEqual(groups, expected_groups)

        # Make sure saving the current term is a no-op:
        self.term.save()
        groups = list(self.user.groups.all())
        self.assertItemsEqual(groups, expected_groups)

        # Add a regular officer position for this user in a new term (not
        # "current"), and the user's group count should increase:
        term_new = Term(term=Term.FALL, year=2012)
        term_new.save()
        officer_reg = Officer(user=self.user, position=self.position_regular,
                              term=term_new)
        officer_reg.save()
        expected_groups.update(self.position_regular.get_corresponding_groups(
            term=term_new))
        groups = list(self.user.groups.all())
        self.assertItemsEqual(groups, expected_groups)

        # Now change the "new" term to be the current term:
        term_new.current = True
        term_new.save()

        # The self.term object is stale now, so re-fetch it from the database:
        self.term = Term.objects.get(pk=self.term.pk)

        # We should expect that the user should still be a "Current Officer",
        # but no longer "Current" for the groups specific to the exec position.
        groups = list(self.user.groups.all())
        # Get "expected_groups" over again, since the current term has changed:
        expected_groups = set(self.position_exec.get_corresponding_groups(
            term=self.term))
        expected_groups.update(self.position_regular.get_corresponding_groups(
            term=term_new))
        self.assertItemsEqual(groups, expected_groups)

        # Double-check some of the "Current" groups:
        self.assertNotIn(self.exec_group_curr, groups)
        self.assertNotIn(self.pos_exec_group_curr, groups)
        self.assertIn(self.officer_group_curr, groups)
        self.assertIn(self.pos_reg_group_curr, groups)


class SettingsTest(TestCase):
    def setUp(self):
        self.env = EnvironmentVarGuard()

    def test_unset(self):
        with self.env:
            self.env.set('QUARK_ENV', 'dev')
            settings = import_fresh_module('quark.settings')

            self.assertTrue(settings.DEBUG)
            self.assertEqual(settings.DATABASES, DEV_DB)

    def test_production(self):
        with self.env:
            self.env.set('QUARK_ENV', 'production')
            settings = import_fresh_module('quark.settings')

            self.assertFalse(settings.DEBUG)
            self.assertEqual(settings.DATABASES, PROD_DB)

    def test_staging(self):
        with self.env:
            self.env.set('QUARK_ENV', 'staging')
            settings = import_fresh_module('quark.settings')

            self.assertFalse(settings.DEBUG)
            self.assertEqual(settings.DATABASES, STAGING_DB)


class FieldsTest(TestCase):
    def test_visual_date_widget(self):
        # Create a test DateField
        visual_date_field = forms.DateField(widget=fields.VisualDateWidget())

        # Test that the appropriate HTML class is set for the input field:
        self.assertEqual(visual_date_field.widget.attrs['class'], 'vDateField')

    def test_visual_split_datetime(self):
        visual_dt_field = fields.VisualSplitDateTimeField()
        # Ensure that the proper widget is used:
        widget = visual_dt_field.widget
        self.assertTrue(isinstance(widget, fields.VisualSplitDateTimeWidget))

        # Test that the appropriate HTML classes are set for the input fields:
        self.assertEqual(widget.widgets[0].attrs['class'], 'vDateField')
        self.assertEqual(widget.widgets[1].attrs['class'], 'vTimeField')

        # Get the time field (since SplitDatetimeField has a DateField and a
        # TimeField):
        time_field = visual_dt_field.fields[1]

        # Check that the proper time formats are allowed by performing
        # to_python() on inputs, which raises a Violation if an improper format
        # is used:
        self.assertIsNotNone(time_field.to_python('03:14am'))
        self.assertIsNotNone(time_field.to_python('1:11am'))
        self.assertIsNotNone(time_field.to_python('05:00 pm'))
        self.assertIsNotNone(time_field.to_python('11:11pm'))

        # 24 hour format not allowed:
        self.assertRaises(ValidationError, time_field.to_python, '23:11')
        # Needs am/pm:
        self.assertRaises(ValidationError, time_field.to_python, '3:14')
        # Must use colon delimiter:
        self.assertRaises(ValidationError, time_field.to_python, '5.30')


@override_settings(TEST_SETTING='testing')
class SettingsTemplateTagsTest(TestCase):
    """Test case for the "settings" template tag."""
    def setUp(self):
        self.base_string = 'Hello world '
        self.context = Context({'base_string': self.base_string})
        self.test_setting = 'testing'

    def test_settings(self):
        """Verify that the settings tag works for valid settings variables."""
        template = Template(
            '{% load settings_values %}{{ base_string }}'
            '{% settings "TEST_SETTING" %}'
        )
        self.assertEquals(self.base_string + self.test_setting,
                          template.render(self.context))

    def test_settings_invalid_setting(self):
        """Verify that the settings tag returns an empty string for settings
        variables that do not exist.
        """
        template = Template(
            '{% load settings_values %}{{ base_string }}'
            '{% settings "NON_EXISTENT_SETTING" %}'
        )
        self.assertEquals(self.base_string, template.render(self.context))

    def test_settings_assign(self):
        """Verify that the settings_assign tag works for valid settings
        variables.
        """
        template = Template(
            '{% load settings_values %}'
            '{% settings_assign "TEST_SETTING" as test_var %}'
            '{{ base_string }}{{ test_var }}'
        )
        self.assertEquals(self.base_string + self.test_setting,
                          template.render(self.context))

    def test_settings_assign_invalid_setting(self):
        """Verify that the settings_assign tag gives an empty string for
        settings variables that do not exist.
        """
        template = Template(
            '{% load settings_values %}'
            '{% settings_assign "NON_EXISTENT_SETTING" as test_var %}'
            '{{ base_string }}{{ test_var }}'
        )
        self.assertEquals(self.base_string, template.render(self.context))


class GetAPIKeyParamsTemplateTagTest(TestCase):
    """Test case for the "get_api_key_params" template tag."""
    def setUp(self):
        self.template = Template(
            '{% load template_utils %}'
            '{% get_api_key_params user as api_params %}'
            '{{ api_params }}'
        )

    def test_get_api_key_params_for_valid_user(self):
        """Verify that the template tag returns a valid string with the API key
        for a valid user.
        """
        user = get_user_model().objects.create_user(
            username='testuser',
            email='test@tbp.berkeley.edu',
            password='password',
            first_name='John',
            last_name='Doe')
        context = Context({'user': user})
        expected_query_params = 'user={}&amp;key={}'.format(
            user.pk, user.api_key.key)
        self.assertEquals(expected_query_params, self.template.render(context))

    def test_get_api_key_params_for_anon_user(self):
        """Verify that the template tag returns an empty string for a user who
        is not authenticated.
        """
        user = AnonymousUser()
        context = Context({'user': user})
        self.assertEquals('', self.template.render(context))


class GetItemTemplateTagTest(TestCase):
    """Test case for the "get_item" template tag."""
    def setUp(self):
        self.test_value = 'test_value'
        self.test_dict = {'test_key': self.test_value}
        self.context = Context({'test_dict': self.test_dict,
                                'key': 'test_key',
                                'bad_key': 'bad_key'})

    def test_lookup_with_valid_key(self):
        template = Template(
            '{% load template_utils %}'
            '{{ test_dict|get_item:key }}'
        )
        self.assertEquals(self.test_value, template.render(self.context))

    def test_lookup_with_invalid_key(self):
        template = Template(
            '{% load template_utils %}'
            '{{ test_dict|get_item:bad_key }}'
        )
        self.assertEquals('None', template.render(self.context))
