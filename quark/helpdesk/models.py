'''@package quark.helpdesk.models
Helpdesk models.

Contains a simple model for a SentMessage object.
'''

import datetime
# TODO(nitishp) remove all te pickles
import pickle

from django.db import models


class SentMessage(models.Model):
    """
    The SentMessage object has one field, the pickled email message that was
    saved earlier.

    You can ask it for the the name/email of the user who sent the email, the
    ip address, the user agent, the email subject, and the send date.

    Also Django likes to do everything in unicode, but pickled objects are
    supposed to be strings.  Blech.
    """
    pickledmessage = models.TextField()

    def __unicode__(self):
        '''__unicode__ method override.
        Returns the ID number as a unicode string.
        '''
        return unicode(self.id)

    def getheader(self, field, alt='Unknown'):
        '''Gets a header of a SentMessage.

        @param field Which field (CC, To, From, etc.)
        @param alt Alternative text if the field is not available. Default is
        "Unknown".
        '''
        pck = pickle.loads(str(self.pickledmessage))
        try:
            msg = pck.message()
        except:
            pck.cc = None
            msg = pck.message()
        return unicode(msg.get(field, alt))

    def ipaddress(self):
        '''Returns IP address  of the message sender.
        '''
        return self.getheader('X-HD-IP-Address')

    def useragent(self):
        '''Returns the browser User-Agent string of the message sender.
        '''
        return self.getheader('X-HD-UserAgent')

    def asker(self):
        '''Returns the name and email address the message sender provided.
        '''
        return self.getheader('From')

    def subject(self):
        '''Returns the subject the message sender provided.
        NB without unicode() the thing returned will be an email.header.Header
        instance
        '''
        return self.getheader('Subject')

    def was_spam(self):
        '''Returns whether X-HD-WasSpam was set to Yes.
        This header will be set to Yes if a bot filled out the Author field of
        the form.
        '''
        # assuming missing X-HD-WasSpam header means it wasn't spam
        return self.getheader('X-HD-WasSpam', 'No')

    def send_date(self):
        '''Returns the date the message was sent.
        Also offers compatibility with ISO-8601 formatted dates.

        The Date header is a string instead of a DateTime object. WHERE IS THE
        JUSTICE?!
        '''
        try:
            # Format is year month day hour minute second microsecond.
            # Also, for this you need str version not unicode version.
            # Mostly this is for backwards compatibility; the first few emails
            # were sent with ISO-8601 times but you can just use ctime for
            # human-readable and computer-parseable time/dates
            return datetime.datetime.strptime(str(self.getheader('Date')),
                                              "%Y-%m-%dT%H:%M:%S.%f").ctime()
        except:
            # If you can't parse the date/time just settle for the raw string
            return self.getheader('Date')

    def raw_text(self):
        '''Returns raw message text, like .mbox format, with incorrect
        Message-ID.
        '''
        pck = pickle.loads(str(self.pickledmessage))
        try:
            msg = pck.message()
        except:
            pck.cc = None
            msg = pck.message()
        return unicode(msg)
