from django.db import models
from filer.fields.image import FilerImageField


class Item(models.Model):
    name = models.CharField(max_length=40)

    description = models.TextField(blank=True)
    picture = FilerImageField(related_name='item_picture')
    wiki = models.URLField(blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
