from django.conf import settings
from django.db import models


class Quote(models.Model):
    quote = models.TextField(blank=False)
    speakers = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                      related_name='+')
    submitter = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')
    time = models.DateField(auto_now_add=True)

    def __unicode__(self):
        return self.quote

    class Meta(object):
        ordering = ('-time',)
        permissions = (
            ('view_quotes', 'Can view all quotes'),
        )
