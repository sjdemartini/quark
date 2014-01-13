from django.conf import settings
from django.db import models


class News(models.Model):
    """A piece of news or advertising to be shared on the website.

    Multiple News pieces can be included together to create a "newsreel."
    """
    title = models.CharField(max_length=100)
    blurb = models.TextField(
        help_text='You can use "markdown syntax" to add formatting, links, '
                  'etc.')
    image = models.ImageField(upload_to='newsreel/')

    # A rank for ordering the items in a newsreel, where higher number
    # corresponds to higher rank/priority.
    rank = models.PositiveIntegerField(blank=True)

    creator = models.ForeignKey(settings.AUTH_USER_MODEL)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta(object):
        # Order News first on rank (high number to low number), and then on
        # date (most recently updated to least recently updated):
        ordering = ('-rank', '-updated')
        verbose_name_plural = 'news'

    def save(self, *args, **kwargs):
        """Set the rank to be a higher number (higher rank) than all existing
        News items.

        Setting the rank higher than the existing max makes new items start
        at the beginning of the ordering of News items.
        """
        if self.pk is None:
            # Get the current max rank value and set the current item's rank to
            # 1 higher than that:
            rank_aggr = News.objects.all().aggregate(models.Max('rank'))
            max_rank = rank_aggr['rank__max'] or 0
            self.rank = 1 + max_rank

        super(News, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.title
