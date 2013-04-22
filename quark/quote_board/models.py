from django.db import models

from quark.auth.models import User


class Quote(models.Model):
    quote = models.TextField(blank=False)
    speakers = models.ManyToManyField(User, related_name='+')
    submitter = models.ForeignKey(User, related_name='+')
    time = models.DateField(auto_now_add=True)

    def __unicode__(self):
        return self.quote

    class Meta:
        ordering = ('-time',)
