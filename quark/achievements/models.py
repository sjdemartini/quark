from django.db import models

from quark.auth.models import User
from quark.base.models import Term


class Achievement(models.Model):
    # These are strings because they're easier to deal with in fixtures.
    CATEGORIES = (
        ('general', 'General'),
        ('event', 'Event'),  # Event attendance.
        ('elections', 'Elections'),  # Anything doing with officerships.
        ('paperwork', 'Paperwork'),  # Project reports, OM/EM attendance.
        ('awards', 'Awards'),  # OOTS, COTS, rock, etc
        ('driving', 'Driving'),  # Shuttling, mileage, etc.
        ('feats', 'Feats of Strength'),  # Cross-bridge banquet shuttling.
    )

    ORGANIZATION_TBP = 'tbp'
    ORGANIZATION_PIE = 'pie'
    ORGANIZATION_ALL = 'all'
    ORGANIZATIONS = (
        (ORGANIZATION_TBP, 'TBP'),
        (ORGANIZATION_PIE, 'PiE'),
        (ORGANIZATION_ALL, 'All'),
    )

    name = models.CharField(
        max_length=64, help_text='The short name of the achievement.')

    description = models.CharField(
        max_length=128, help_text='The full description of the achievement.')

    organization = models.CharField(
        choices=ORGANIZATIONS, max_length=4, db_index=True,
        default=ORGANIZATION_ALL,
        help_text='Each achievement can be live on TBP, PiE, or all.')

    category = models.CharField(
        choices=CATEGORIES, max_length=64, db_index=True,
        help_text='Each achievement will be listed in exactly one category.')

    sequence = models.CharField(
        max_length=128, blank=True,
        help_text=('In addition to the major category classification, each '
                   'achievement can optionally be part of a sequence. For '
                   'example, you can have achievements for attending 10, 25, '
                   '50, and 100 events. These will be grouped together during '
                   'the rendering phase. Achievements are not required to be '
                   'part of a sequence. Adjacent sequence values (by rank) '
                   'that match will be grouped together.'))

    points = models.IntegerField(
        help_text=('The number of points this achievement is worth. Can be '
                   'positive or negative.'))

    secret = models.BooleanField(
        default=False, db_index=True,
        help_text=('The description for secret achievements are hidden until '
                   'unlocked.'))
    private = models.BooleanField(
        default=False, db_index=True,
        help_text=('Private achievements can only be seen by the user who has '
                   'it.'))
    manual = models.BooleanField(
        default=False, db_index=True,
        help_text='Manual achievements can only be assigned by a human.')
    repeatable = models.BooleanField(
        default=False, db_index=True,
        help_text=('True if you can get this achievement multiple times - '
                   'attending all fun events for N semesters should show up N'
                   'times'))

    rank = models.FloatField(
        default=0, db_index=True,
        help_text=('The rank of the achievement, for the display order. The '
                   'higher the number, the lower down on the page it shows.'))

    icon = models.ImageField(
        upload_to='images/achievements/', blank=True, null=True)
    icon_creator = models.ForeignKey(
        User, blank=True, null=True,
        help_text='The creator of the icon used for this achievement.')

    class Meta:
        ordering = ('rank',)

    def __unicode__(self):
        return self.name


class UserAchievement(models.Model):
    """UserAchievement instances contain data about an acquired achievement.

    In some cases, a user can get the same achievement multiple times, so we
    don't put any constraints on uniqueness. In most cases, manual achievements
    should only be awarded once per person at most, but that will be enforced
    at the app level and not the database level.
    """
    user = models.ForeignKey(User)
    achievement = models.ForeignKey(Achievement)

    acquired = models.BooleanField(
        default=True, db_index=True,
        help_text=('Defaults to True. This is only false when we want to '
                   'store the progress and goal amounts.'))

    progress = models.IntegerField(
        help_text='Integer progress for this achievement (17 events).')
    goal = models.IntegerField(
        help_text=('Integer goal for this achievement. 0 means that the '
                   'progress bar should be hidden.'))

    assigner = models.ForeignKey(
        User, related_name='assigner', null=True, blank=True,
        help_text=('The person who assigned this achievement. Null if the '
                   'system assigned it.'))

    term = models.ForeignKey(
        Term, null=True, blank=True,
        help_text='The term in which this achievement was earned, or null.')

    data = models.CharField(
        max_length=512, blank=True,
        help_text=('Can hold whatever extra metadata or notes about this '
                   'achievement.'))

    # TODO(wli): write or hook this up to a notifications framework.
    notified_user = models.BooleanField(
        default=False, db_index=True,
        help_text='True if the user has been notified about this achievement.')

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = (
            ('add_user_achievement', 'Can add user achievements'),
            ('delete_user_achievement', 'Can delete user achievements '),
        )

    def __unicode__(self):
        # pylint: disable=E1101
        return '%s - %s' % (self.user.get_common_name(), self.achievement.name)
