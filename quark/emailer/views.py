import pickle
import random

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.core.mail import make_msgid
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

# TODO(nitishp) uncomment things as functionality is added to quark
# from quark.base.decorators import officer_required
from quark.base.models import Officer
from quark.base.models import Term
from quark.emailer.forms import ContactCaptcha, ContactForm
# from quark.events.views import get_event
from quark.events.models import Event  # until get_event is added
from quark.helpdesk.models import SentMessage


# pylint: disable=R0912,R0914
def submit_helpdesk(request):
    # TODO(nitishp) Convert to class based views after tests are done
    """
    FIXME: MERGE WITH SUBMIT_EVENT BELOW
    """

    # First checks if it's POSTed. Then checks if the form is valid using
    # Django's built-in form stuff. If no name is provided, the email address
    # becomes the "name".

    # According to Django docs, BadHeaderError is what you get if you try to,
    # for example, modify other headers from the From field using newlines:

    # <blockquote>From: evilguy@example.com\nTo: spamtarget@example.com
    # </blockquote>

    if request.method == 'POST':
        form = ContactCaptcha(request.POST)
        status = 1
        result_message = 'Operation incomplete!'
        spam = request.POST.get('author', '')

        if not form.is_valid() or spam:
            if not form.is_valid():
                # with an invalid form, form will be blank so we can't do
                # anything else but give them an error message
                return render_to_response(
                    'helpdesk/base.html', {'form': form},
                    context_instance=RequestContext(request))
            if spam:
                result_message = 'Successfully sent!'
                status = 0  # following example in events
                # need to continue to set all email variables before we can
                # quit this view

        # Set up variables for email
        email = form.cleaned_data['email']
        name = form.cleaned_data['name']
        question = form.cleaned_data['message']
        subject = form.cleaned_data['subject']
        ip_addr = request.META.get('HTTP_X_FORWARDED_FOR')
        if not ip_addr:
            ip_addr = unicode(request.META.get('REMOTE_ADDR', 'None provided'))
        else:
            ip_addr = unicode(ip_addr)
        useragent = unicode(request.META.get('HTTP_USER_AGENT',
                                             'None provided'))
        to_email = [settings.HELPDESK_ADDRESS]

        # Variables that are based on the above
        from_email = '%s <%s>' % (name, email)
        reply_to = from_email  # they should be the same right?
        headers = {'Reply-To': reply_to,
                   'X-Helpdesk-IP-Address': ip_addr,
                   'X-Helpdesk-UserAgent': useragent,
                   'Message-Id': make_msgid()}

        completemessage = EmailMessage(
            subject=subject,
            body=question,
            from_email=from_email,
            to=to_email,
            headers=headers)

        # only assign to stars members
        officers = Officer.objects.filter(
            term=Term.objects.get_current_term(),
            position__short_name="stars")

        if officers:  # if officers non-empty
            # select a random officer. we have enough that double assignments
            # shouldn't happen very often.
            assignee = random.choice(officers)
            assigning_to = ["%s@tbp.berkeley.edu" % assignee.user.username]
            assigning_body = (
                'HelpdeskQ has automatically assigned %s as the point '
                'person for the helpdesk question with subject \"%s\". '
                'Please compile a response for this question within 48 '
                'hours. This is a random assignment among STARS committee '
                'members. Other officers should continue to contribute '
                'knowledge about this question, but you are responsible for '
                'sending the final answer. The body of the question is '
                'below for reference.\n\n' %
                (assignee.user.get_common_name(), subject))
        else:
            assigning_to = [settings.IT_ADDRESS, settings.STARS_ADDRESS]
            assigning_body = (
                'Automatic-assignment for HelpdeskQ has failed. There are '
                'no STARS officers listed for the current semester, so '
                'auto-assignment to a STARS officer could not be completed. '
                'This is most likely a problem that needs to be fixed. '
                'The Helpdesk question (the body of which is copied below) '
                'was still sent to all officers.')

        assigning_body += question
        assigning_message = EmailMessage(
            subject=subject,
            body=assigning_body,
            from_email="helpdeskq@tbp.berkeley.edu",
            to=assigning_to,
            cc=[settings.HELPDESK_ADDRESS])

        if spam:
            # change destination of message to the spam destination in
            # settings.py
            to_email = [settings.HELPDESK_SPAM_TO]
            headers['X-Helpdesk-WasSpam'] = 'Yes'
            headers['X-Helpdesk-Author'] = spam
            if settings.HELPDESK_SEND_SPAM_NOTICE:
                spamnotice = EmailMessage(
                    subject='[Helpdesk spam] ' + subject,
                    body=('Help! We have been spammed by \"%s\" from %s!'
                          '\n\n------------\n\n%s' %
                          (from_email, headers['X-Helpdesk-IP-Address'],
                           unicode(completemessage.message()))),
                    from_email='root@tbp.berkeley.edu',
                    to=[settings.HELPDESK_NOTICE_TO],
                    headers=headers)
                # server will return 500 error if spamnotice cannot be sent.
                spamnotice.send()
            form = ContactCaptcha()
            # recreate completmessage with new headers
            completemessage = EmailMessage(subject=subject,
                                           body=question,
                                           from_email=from_email,
                                           to=to_email,
                                           headers=headers)

        if not spam and settings.HELPDESK_CC_ASKER:
            # cc address might be an innocent bystander's if it's spam
            ccmessage = EmailMessage(
                subject='[Helpdesk] ' + subject,
                body=('Hi %s,\n\nYour question has been submitted.\n\nSomeone'
                      'will get back to you as soon as possible!'
                      '\n\n------------\n\n%s' % (name, question)),
                from_email='TBP Helpdesk <%s>' % settings.HELPDESK_ADDRESS,
                to=[from_email],)
            try:
                ccmessage.send()
            except:
                pass  # sending is nonessential due to confirmation page

        try:
            if not spam or settings.HELPDESK_SEND_SPAM:
                completemessage.send()
                m_id = completemessage.extra_headers.get('Message-Id',
                                                         None)
                assigning_message.extra_headers = {'References': m_id,
                                                   'In-Reply-To': m_id}
                if settings.ENABLE_HELPDESKQ:
                    assigning_message.send(fail_silently=True)
            result_message = 'Successfully sent!'
            status = 0  # following example in events
            # so that if you submit it succesfully you don't get your text
            # back again:
            form = ContactCaptcha()
        except:
            result_message = ('Your message could not be sent for an '
                              'unknown reason. Please try again later.')
            status = 1

        try:
            # TODO(nitishp): Make this not use pickling - edit helpdesk models
            del completemessage.connection
            sentmsg = SentMessage(
                pickledmessage=str(pickle.dumps(completemessage)))
            sentmsg.save()
        except:
            pass  # do nothing if saving fails
        return render_to_response(
            'helpdesk/base.html',
            {'result_message': result_message, 'form': form, 'status': status},
            context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(reverse('helpdesk-index'))


@login_required
# pylint disable=R0914
# TODO(nitishp) restore when user access is sorted out
# @officer_required
def submit_event(request, event_id):
    # TODO(nitishp) restore when views are added for events
    # event = get_event(request, event_id)
    event = get_object_or_404(Event, pk=event_id)  # currently same as above
    signedup_list = event.eventsignup_set.order_by('name')
    cc_email = [event.committee.short_name + '@tbp.berkeley.edu']
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Set up variables for email
            # email and name could be submitted via form like helpdesk but
            # aren't.
            email = request.user.email
            name = request.user.get_full_name()
            message = form.cleaned_data['message']
            subject = form.cleaned_data['subject']
            ip_addr = request.META.get('HTTP_X_FORWARDED_FOR')
            if not ip_addr:
                ip_addr = unicode(request.META.get('REMOTE_ADDR',
                                                   'None provided'))
            else:
                ip_addr = unicode(ip_addr)
            useragent = unicode(
                request.META.get('HTTP_USER_AGENT',
                                 'None provided'))

            bcc = []
            for signup in signedup_list:
                if signup.person:
                    # check if person has an account or if they signed up with
                    # their email address
                    bcc.append(signup.person.email)
                else:
                    bcc.append(signup.email)
            # Also CC email to organizing committee

            if len(bcc) == 0:
                # empty recipients list, most likely due to no participants
                status = 1
                result_message = 'Nobody hears you.'
            else:
                # Variables that are based on the above
                from_email = '%s <%s>' % (name, email)
                headers = {'X-EC-IP-Address': ip_addr,
                           'X-EC-UserAgent': useragent}

                completemessage = EmailMessage(subject=subject,
                                               body=message,
                                               from_email=from_email,
                                               cc=cc_email,
                                               bcc=bcc,
                                               headers=headers)

                try:
                    completemessage.send()
                    status = 0
                    result_message = 'Successfully sent!'
                    form = ContactForm()
                except:
                    status = 1
                    result_message = 'Failure!'
        else:
            status = 1
            # use the default forms error message in this case:
            result_message = False
        return render_to_response(
            'events/contact.html',
            {'result_message': result_message,
             'form': form,
             'status': status,
             'event': event,
             'signedup_list': signedup_list,
             'cc_list': cc_email},
            context_instance=RequestContext(request))
    else:
        # a form with this content should generate an error so set new=True to
        # suppress error output until user has submitted the form
        form = ContactForm(
            {'name': request.user.get_full_name(),
             'email': request.user.email,
             'subject': u'[TBP] %s: Important announcement' % event.name,
             'message': '',
             'signedup_list': signedup_list})
        return render_to_response(
            'events/contact.html',
            {'event': event,
             'form': form,
             'signedup_list': signedup_list,
             'new': True,
             'cc_list': cc_email},
            context_instance=RequestContext(request))
