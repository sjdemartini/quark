import csv
import re

from django import forms

from quark.pie_register.models import TeamRegistration

# pylint: disable=R0924


class TeamForm(forms.ModelForm):
    REQUIRED_CSS_CLASS = 'required'
    NAME_REGEX = r'^[a-zA-Z\'.\- ]+$'
    DAYS_OF_WEEK_REGEX = r'^(M|T|W|Th|F|Sa|Su)$'
    MIN_STUDENT_GRADE_LEVEL = 9
    MAX_STUDENT_GRADE_LEVEL = 12

    def clean_student_roster(self):
        #TODO(bcortright): Change team registration to be more user-friendly and
        #less hacky by removing the need to do so much custom field validation.
        # removes trailing whitespaces and new lines
        student_roster = self.cleaned_data['student_roster'].strip()
        self.cleaned_data['student_roster'] = student_roster
        lines = csv.reader(student_roster.split('\n'))

        try:
            for line in lines:
                if len(line) == 0:
                    continue
                # <firstname>, <lastname>, <grade>
                if len(line) != 3:
                    raise forms.ValidationError(
                        ('Invalid line %d: %s.\nPlease make sure each '
                         'student is on his/her own line and each line '
                         'has a first name, last name, and grade') % (
                            lines.line_num, line))

                # Grab the variables from the csv
                first_name, last_name, grade = [s.strip() for s in line]
                # Make sure we don't have any empty cells
                if not first_name or not last_name or not grade:
                    raise forms.ValidationError(
                        'Invalid line %d (empty cells): %s' % (
                            lines.line_num, line))

                if ((not re.match(TeamForm.NAME_REGEX, first_name) or
                     not re.match(TeamForm.NAME_REGEX, last_name))):
                    raise forms.ValidationError(
                        ('Invalid line %d: %s.\n'
                         'Name may only contain alphabet characters, '
                         'spaces, apostrophes and hyphens.') % (
                            lines.line_num, line))
                try:
                    grade = int(grade)
                except ValueError:
                    raise forms.ValidationError(
                        ('Invalid line %d: %s.\n'
                         'Grade must be a value between %d-%d') % (
                            lines.line_num, line,
                            TeamForm.MIN_STUDENT_GRADE_LEVEL,
                            TeamForm.MAX_STUDENT_GRADE_LEVEL))
                if ((grade < TeamForm.MIN_STUDENT_GRADE_LEVEL or
                     grade > TeamForm.MAX_STUDENT_GRADE_LEVEL)):
                    raise forms.ValidationError(
                        ('Invalid line %d: %s.\n'
                         'Grade must be a value between %d-%d') % (
                            lines.line_num, line,
                            TeamForm.MIN_STUDENT_GRADE_LEVEL,
                            TeamForm.MAX_STUDENT_GRADE_LEVEL))
                # We have a valid line
        except csv.Error:
            raise forms.ValidationError('Invalid line %d' % (lines.line_num))
        return student_roster

    def clean_possible_times(self):
        possible_times = self.cleaned_data['possible_times'].strip()
        self.cleaned_data['possible_times'] = possible_times
        lines = csv.reader(possible_times.split('\n'))
        try:
            for line in lines:
                if len(line) == 0:
                    continue
                # day, times (may be more than one set of time ranges)
                if len(line) < 2:
                    raise forms.ValidationError(
                        ('Invalid line %d: %s.\nPlease make sure each '
                         'day is on its own line and each line '
                         'has a day of the week and at least one time') % (
                            lines.line_num, line))

                # Grab the variables from the csv
                entries = [s.strip() for s in line]
                day = entries[0]
                times = entries[1:]
                # Make sure we don't have any empty cells
                if not day or not times:
                    raise forms.ValidationError(
                        'Invalid line %d (empty cells): %s' % (
                            lines.line_num, line))

                if not re.match(TeamForm.DAYS_OF_WEEK_REGEX, day):
                    raise forms.ValidationError(
                        ('Invalid line %d: %s.\n'
                         'Please make sure to use a properly formatted '
                         'day of the week.') % (
                            lines.line_num, line))

                for time_slot in times:
                    try:
                        start_time, end_time = time_slot.split('-')
                        num_start = int(start_time)
                        num_end = int(end_time)
                    except:
                        raise forms.ValidationError(
                            'Invalid line %d: %s.\n Please make'
                            'sure to have times available listed' %
                            (lines.line_num, line))
                    if ((min(num_start, num_end) < 800 or
                         max(num_start, num_end) > 2400)):
                        raise forms.ValidationError(
                            'PiE does not meet before 800. please '
                            'enter a later time.')
                    if num_start % 100 >= 60 or num_end % 100 >= 60:
                        raise forms.ValidationError(
                            'Invalid line %d: %s. Please make sure to '
                            'input valid lines.' % (lines.line_num, line))
                    if num_end - num_start < 200:
                        raise forms.ValidationError(
                            'Your meeting time must be at least two '
                            'hours long.')

                # We have a valid line
        except csv.Error:
            raise forms.ValidationError('Invalid line %d' % (lines.line_num))
        return possible_times

    class Meta(object):
        model = TeamRegistration
        # Want the fields in particular order
        fields = ('school_name', 'team_name', 'teacher_name',
                  'teacher_email', 'phone_number', 'applicant_email', 'heard',
                  'heard_other', 'experience', 'tools', 'teacher_drive',
                  'parents_drive', 'work_area', 'student_roster',
                  'why_interested', 'possible_times')
