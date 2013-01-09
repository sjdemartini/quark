from django.db import models
from easy_thumbnails.fields import ThumbnailerImageField


class Item(models.Model):
    name = models.CharField(max_length=40)

    description = models.TextField(blank=True)
    picture = ThumbnailerImageField(upload_to='pie/items', blank=True)
    wiki = models.URLField(blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return 'Item %s' % self.name
