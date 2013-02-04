import datetime

from django.db import models

from quark.base_pie.models import Team


class Alliance(models.Model):
    autonomous = models.IntegerField(default=0)
    bonus = models.IntegerField(default=0)
    manual = models.IntegerField(default=0)
    penalty = models.IntegerField(default=0)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def get_total_score(self):
        return self.autonomous + self.manual + self.bonus - self.penalty

    def __unicode__(self):
        return 'Alliance score: ' % (self.get_total_score())


class AllianceMember(models.Model):
    alliance = models.ForeignKey(Alliance, related_name='alliance_member')
    disqualified = models.BooleanField(default=False)
    team = models.ForeignKey(Team, related_name='+')

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return 'Alliance member: Team %s, disqualified: %s' % (
            unicode(self.team), self.disqualified)


class Match(models.Model):
    blue = models.ForeignKey(Alliance, related_name='+')
    completed = models.BooleanField(default=False)
    description = models.TextField(default='Match')
    final = models.BooleanField(default=False)
    gold = models.ForeignKey(Alliance, related_name='+')
    match_time = models.DateTimeField(default=datetime.datetime.now())

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '(%d - %d) [%s]' % (
            self.blue.get_total_score(),
            self.gold.get_total_score(),
            self.match_time.time())
