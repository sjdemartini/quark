from django.contrib.auth.models import User
from django.contrib.localflavor.us.models import PhoneNumberField
from django.db import models

from quark.base_pie.models import Season


class TeamRegistration(models.Model):
    EXPERIENCE_CHOICES = (
        ('PIE', 'Yes, Pioneers In Engineering'),
        ('First', 'Yes, FIRST'),
        ('VEX', 'Yes, VEX'),
        ('BotBall', 'Yes, BotBall'),
        ('No', 'No, this will be their first robotics experience'),
        ('Other', 'Other'),
    )
    HEARD_CHOICES = (
        ('Participated', 'Participated in previous year'),
        ('Email', 'Received an email from us'),
        ('Website', 'Our website'),
        ('Teacher', 'Heard about us from a teacher'),
        ('Other', 'Other'),
    )
    TOOL_CHOICES = (
        (0, 'Yes'),
        (1, 'No, but school can obtain tools'),
        (2, 'No, and school cannot obtain tools'),
    )

    applicant_email = models.EmailField()
    experience = models.CharField(
        max_length=20,
        choices=EXPERIENCE_CHOICES,
        verbose_name='Has your team done robotics before?')
    heard = models.CharField(
        max_length=20,
        choices=HEARD_CHOICES,
        verbose_name='How did you hear about PIE?')
    heard_other = models.CharField(
        max_length=100,
        verbose_name='If other, then where did you hear about PiE?')
    parents_drive = models.BooleanField(
        verbose_name=(
            'Can the parents drive students to UC Berkeley '
            'for events or work sessions?'))
    phone_number = PhoneNumberField(
        verbose_name='Phone number of teacher')
    school_name = models.CharField(max_length=80)
    student_roster = models.TextField(
        verbose_name='Names and grades of participating students',
        help_text=(
            'Please put each student on their own line, with each line '
            'in the following format: first_name, last_name, grade <br>'
            '<em>Example:</em> Oski, Bear, 12'))
    teacher_drive = models.BooleanField(
        verbose_name=(
            'Can the teacher drive students to UC Berkeley '
            'for events or work sessions?'))

    teacher_email = models.EmailField()
    teacher_name = models.CharField(max_length=40,
                                    verbose_name='Teacher advisor')
    team_name = models.CharField(max_length=40, blank=True)
    tools = models.PositiveSmallIntegerField(
        choices=TOOL_CHOICES,
        verbose_name=(
            'Does your school have access to a basic set of '
            'tools? If not, can the school obtain them?'))
    why_interested = models.TextField(
        verbose_name=(
            'Briefly describe why you are interested in participating in PiE'))
    work_area = models.BooleanField(
        verbose_name=(
            'Does your school have a space where your team can work on '
            'the robot?'))

    possible_times = models.TextField(
        verbose_name=(
            'What times can your team meet with their mentors for at least two '
            'consecutive hours for work sessions?'),
        help_text=(
            'Please use either M, T, W, Th, F, Sa, Su for the days '
            'of the week and the times as a range with each day '
            'on its own line and in military time. <br> '
            '<em> Example </em>:<br> &nbsp;Th, 1400-1800, 1700'
            '-1900<br> &nbsp;F, 1500-1900'))

    applicant = models.ForeignKey(User, null=True)
    season = models.ForeignKey(Season)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
