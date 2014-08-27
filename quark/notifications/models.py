from django.conf import settings
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Notification(models.Model):
    NEGATIVE = 'negative'
    NEUTRAL = 'neutral'
    POSITIVE = 'positive'

    STATUS_TYPES = (
        (NEGATIVE, 'Negative'),
        (NEUTRAL, 'Neutral'),
        (POSITIVE, 'Positive'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    status = models.CharField(choices=STATUS_TYPES, max_length=8)

    content_type = models.ForeignKey(ContentType)
    object_pk = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_pk')

    title = models.CharField(
        max_length=128,
        help_text=('The title for describing the type of notification (e.g. '
                   '"Achievement Unlocked" or "Missing Project Report").'))
    subtitle = models.CharField(
        max_length=256,
        help_text=('The sub title for describing what the notification is '
                   'associated with (e.g. an achievement name or project '
                   'report title).'))
    description = models.CharField(
        max_length=512,
        help_text=('The description for providing any additional information '
                   'about the notification (e.g. how an achievement is '
                   'unlocked or how long a project report is overdue).'))
    image_url = models.CharField(
        blank=True,
        max_length=255,
        help_text=('The URL of any image for this notification (e.g. an '
                   'achievement icon).'))
    url = models.CharField(
        blank=True,
        max_length=255,
        help_text=('The URL that the user is redirected to when clicking the '
                   'notification.'))

    cleared = models.BooleanField(
        default=False, db_index=True,
        help_text='Whether the user has closed this notification.')

    class Meta(object):
        unique_together = ('user', 'content_type', 'object_pk')

    def __unicode__(self):
        return 'Notification for {}: {} ({})'.format(
            self.user.get_username(), self.title, self.subtitle)
