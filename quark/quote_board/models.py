from django.db import models

from quark.auth.models import User


class Quote(models.Model):
    submitter = models.ForeignKey(User, related_name='+')
    speakers = models.ManyToManyField(User, related_name='+')
    quote = models.TextField(blank=False)
    time = models.DateField(auto_now_add=True)

    def __unicode__(self):
        return self.quote
