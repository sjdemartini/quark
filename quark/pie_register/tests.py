from django.test import TestCase

from quark.pie_register.forms import TeamForm


class TeamFormRosterTest(TestCase):
    """
    Class is dedicated to the thorough testing of TestForm, with emphasis on
    the student roster.
    """
    def generate_form(self, roster):
        """
        Makes the process of testing the staff roster for the form
        easier.
        ======
        Arguments:
            roster is expected to be a string.
        """
        return TeamForm({
            'school_name': 'Nyan High School',
            'student_roster': roster,
            'teacher_name': 'John Wang',
            'why_interested': ('Well... John Wang was this awkward tenor drums '
                               'percussionist in band and he happened to know '
                               'I was into robotics...'),
            'teacher_email': 'wangj@example.com',
            'applicant_email': 'dwai@example.com',
            'phone_number': '314-159-2653',
            'team_name': 'meow',
            'heard': 'Other',
            'heard_other': 'blah blah blah',
            'experience': 'VEX',
            'teacher_drive': True,
            'tools': 0,
            'parents_drive': False,
            'work_area': False,
            'possible_times': 'F, 1200-1500'
        })

    def test_too_few_in_row(self):
        roster = 'hi'
        self.assertFalse(self.generate_form(roster).is_valid())

        roster = 'hello, there'
        self.assertFalse(self.generate_form(roster).is_valid())

    def test_stripping_extra_whitespace(self):
        roster = '\n\n\n\n\n\n\n nyan, cat, 12'
        form = self.generate_form(roster)
        self.assertTrue(form.is_valid())
        self.assertEqual('nyan, cat, 12', form.cleaned_data['student_roster'])

        roster = '\t\t\t\t nyan, cat, 12 \t\t\t\t\t'
        form = self.generate_form(roster)
        self.assertTrue(form.is_valid())
        self.assertEqual('nyan, cat, 12', form.cleaned_data['student_roster'])

        availability = 'nyan, cat, 12 \n\n\n\n\n\n\n\n\n\n\n\n            '
        form = self.generate_form(availability)
        self.assertTrue(form.is_valid())
        self.assertEqual('nyan, cat, 12', form.cleaned_data['student_roster'])

    def test_multiple_short_rows(self):
        roster = ('hello, there\n'
                  'Humpty, Dumpty')
        self.assertFalse(self.generate_form(roster).is_valid())

        roster = ('hello, there\n'
                  'Humpty, Dumpty\n'
                  'what, up')
        self.assertFalse(self.generate_form(roster).is_valid())

    def test_non_standard_characters(self):
        roster = 'hello, there, wli!'
        self.assertFalse(self.generate_form(roster).is_valid())

        roster = 'i, <3, #twitter'
        self.assertFalse(self.generate_form(roster).is_valid())

    def test_fancy_acceptable_names(self):
        roster = 'Doug, Hutchingson Jr., 11'
        self.assertTrue(self.generate_form(roster).is_valid())

        roster = 'Dr. El, Roboto, 10'
        self.assertTrue(self.generate_form(roster).is_valid())

        roster = 'Mr. Uber, Fancy-pants, 10'
        self.assertTrue(self.generate_form(roster).is_valid())

    def test_normal_names(self):
        roster = 'Ryan, Julian, 12'
        self.assertTrue(self.generate_form(roster).is_valid())

        roster = 'Aditya, Yellapragada, 12'
        self.assertTrue(self.generate_form(roster).is_valid())

    def test_good_grade(self):
        roster = 'Nyan, Cat, 11'
        self.assertTrue(self.generate_form(roster).is_valid())

        roster = 'Nyan, Cat, 10'
        self.assertTrue(self.generate_form(roster).is_valid())

    def test_bad_grade(self):
        roster = 'Nyan, Cat, 100'
        self.assertFalse(self.generate_form(roster).is_valid())

        roster = 'Nyan, Cat, 5'
        self.assertFalse(self.generate_form(roster).is_valid())

        roster = 'Nyan, Cat, --'
        self.assertFalse(self.generate_form(roster).is_valid())

        roster = 'Nyan, Cat, abc'
        self.assertFalse(self.generate_form(roster).is_valid())


class TeamFormAvailabilityTest(TestCase):
    """
    Class is dedicated to the thorough testing of TestForm, with emphasis on
    the team availability.
    """
    def generate_form(self, availability):
        """
        Makes the process of testing the staff roster for the form
        easier.
        ======
        Arguments:
            roster is expected to be a string.
        """
        return TeamForm({
            'school_name': 'Nyan High School',
            'student_roster': 'John, Wang, 11',
            'teacher_name': 'John Wang',
            'why_interested': ('Well... John Wang was this awkward tenor drums '
                               'percussionist in band and he happened to know '
                               'I was into robotics...'),
            'teacher_email': 'wangj@example.com',
            'applicant_email': 'dwai@example.com',
            'phone_number': '314-159-2653',
            'team_name': 'meow',
            'heard': 'Other',
            'heard_other': 'yes.',
            'experience': 'VEX',
            'teacher_drive': True,
            'tools': 0,
            'parents_drive': False,
            'work_area': True,
            'possible_times': availability
        })

    def test_good_availability(self):
        availability = 'T, 1500-1800'
        self.assertTrue(self.generate_form(availability).is_valid())

        availability = 'T, 800-2400, 1800-2100'
        self.assertTrue(self.generate_form(availability).is_valid())

        availability = ('T, 1400-1600, 1700-1900\n'
                        'F, 800-1000')
        self.assertTrue(self.generate_form(availability).is_valid())

    def test_stripping_white_space(self):
        availability = '\n\n\n\n\n\n\n T, 1500-1800'
        form = self.generate_form(availability)
        self.assertTrue(form.is_valid())
        self.assertEqual('T, 1500-1800', form.cleaned_data['possible_times'])

        availability = 'T, 1500-1800 \n\n\n\n\n\n\n\n\n\n\n\n            '
        form = self.generate_form(availability)
        self.assertTrue(form.is_valid())
        self.assertEqual('T, 1500-1800', form.cleaned_data['possible_times'])

    def test_bad_days(self):
        availability = 'TT, 1300-1500'
        self.assertFalse(self.generate_form(availability).is_valid())

        availability = 'Sat, 1300-1500'
        self.assertFalse(self.generate_form(availability).is_valid())

        availability = ('F, 1300-1500\n'
                        'Sat, 1300-1400')
        self.assertFalse(self.generate_form(availability).is_valid())

    def test_missing_days(self):
        availability = '1300-1500'
        self.assertFalse(self.generate_form(availability).is_valid())

        availability = ('T, 1100-1300\n'
                        '1400-1600')
        self.assertFalse(self.generate_form(availability).is_valid())

    def test_bad_times(self):
        availability = 'F, 99-99'
        self.assertFalse(self.generate_form(availability).is_valid())

        availability = 'Sa, 2-86'
        self.assertFalse(self.generate_form(availability).is_valid())

        availability = 'Sa, 99-200'
        self.assertFalse(self.generate_form(availability).is_valid())

        availability = ('T, 1500-1700'
                        'F, 900-4400')
        self.assertFalse(self.generate_form(availability).is_valid())

        availability = '1'
        self.assertFalse(self.generate_form(availability).is_valid())

        availability = 'T, 1200-1400, 1500'
        self.assertFalse(self.generate_form(availability).is_valid())

        availability = 'T, 2270-2300'
        self.assertFalse(self.generate_form(availability).is_valid())

        availability = 'T, 1700-1800'
        self.assertFalse(self.generate_form(availability).is_valid())

        availability = 'T, 700-2400'
        self.assertFalse(self.generate_form(availability).is_valid())

    def test_missing_times(self):
        availability = 'F, '
        self.assertFalse(self.generate_form(availability).is_valid())

        availability = ('M, 1100-1200,\n'
                        'T')
        self.assertFalse(self.generate_form(availability).is_valid())

        availability = ('M\n'
                        'T, 1300-1400')
        self.assertFalse(self.generate_form(availability).is_valid())
