from django.db import models

from quark.base_pie.models import Season
from quark.events.models import Event


class PiEEvent(Event):
    season = models.ForeignKey(Season)

    # TODO(sjdemartini): set term field for PiEEvents using
    # self.season.get_corresponding_term(). This is to be accomplished in the
    # forms for PiEEvent

    def __unicode__(self):
        return u'%s - %s' % (self.name, unicode(self.season))


# Use EventSignUp and EventAttendance from quark.events.models to track sign
# ups and attendance on PiEEvents
