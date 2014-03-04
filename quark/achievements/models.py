from django.conf import settings
from django.db import models

from quark.base.models import Term


class Achievement(models.Model):
    """An achievement shows significant user accomplishment in some way."""
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

    PRIVACY_PUBLIC = 'public'
    PRIVACY_PRIVATE = 'private'
    PRIVACY_SECRET = 'secret'
    PRIVACY_SETTINGS = (
        (PRIVACY_PUBLIC, 'Public'),
        (PRIVACY_PRIVATE, 'Private'),
        (PRIVACY_SECRET, 'Secret'),
    )

    short_name = models.CharField(
        max_length=32, db_index=True, primary_key=True,
        help_text='A short name to be used to search for the achievement in '
                  'the database.')

    name = models.CharField(
        max_length=64, help_text='The name of the achievement to be displayed '
                                 'on the page.')

    description = models.CharField(
        max_length=128, help_text='The full description of the achievement.')

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

    goal = models.IntegerField(
        default=0,
        help_text=('Integer goal for this achievement. 0 means that the '
                   'progress bar should be hidden.'))

    privacy = models.CharField(
        choices=PRIVACY_SETTINGS, max_length=8, db_index=True,
        default=PRIVACY_PUBLIC,
        help_text=('Each achievement can be public, secret, or private. '
                   'A public achievement is viewable by everyone. A secret '
                   'achievement\'s name and description is hidden until '
                   'unlocked. A private achievement can\'t be seen except '
                   'by the user who has it.'))

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

    icon_filename = models.CharField(
        max_length=128, blank=True,
        help_text=('The image file for the achievement icon, which should be '
                   'located in quark/static/images/achievements.'))

    icon_creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True,
        help_text='The creator of the icon used for this achievement.')

    class Meta(object):
        ordering = ('rank',)

    def __unicode__(self):
        return self.name

    def assign(self, user, acquired=True, progress=0, term=None):
        """Assign this achievements to a user."""
        if term is None:
            term = Term.objects.get_current_term()

        # get or create a new user achievement for this achievement given to
        # the specified user. if no previous achievement exists, the default
        # is to set acquired to false so that it is updated below
        user_achievement, _ = UserAchievement.objects.get_or_create(
            achievement=self, user=user)

        if user_achievement.acquired is False:
            # if the achievement has not already been acquired by this user, set
            # the user achievement's progress, term, and acquisition state
            user_achievement.acquired = acquired
            user_achievement.progress = progress
            user_achievement.term = term
            user_achievement.save()
        elif acquired is False and user_achievement.term == term:
            # if the achievement has already been acquired but is being set
            # to unacquired in the same term, it gets overridden
            user_achievement.acquired = acquired
            user_achievement.progress = progress
            user_achievement.save()

        return True


class UserAchievement(models.Model):
    """UserAchievement instances contain data about an acquired achievement.

    In some cases, a user can get the same achievement multiple times, so we
    don't put any constraints on uniqueness. In most cases, manual achievements
    should only be awarded once per person at most, but that will be enforced
    at the app level and not the database level.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    achievement = models.ForeignKey(Achievement)

    acquired = models.BooleanField(
        default=False, db_index=True,
        help_text=('True if the user has done everything needed to receive '
                   'the achievement. False if there is only progress towards '
                   'the goal.'))

    progress = models.IntegerField(
        default=0,
        help_text=('For unacquired achievements, this field gives the user\'s '
                   'progress towards the achievement\'s goal. (e.g. 17 events '
                   'out of 25 required for the achievement.)'))

    assigner = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='assigner', null=True,
        blank=True, help_text=('The person who assigned this achievement. '
                               'Null if the system assigned it.'))

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

    class Meta(object):
        permissions = (
            ('add_user_achievement', 'Can add user achievements'),
            ('delete_user_achievement', 'Can delete user achievements '),
        )

    def __unicode__(self):
        return '{} - {}'.format(self.user.get_full_name(),
                                self.achievement.name)
