from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^event/$', 'quark.emailer.views.submit_event',
        name='helpdesk-index'),
    url(r'^helpdesk/$', 'quark.emailer.views.submit_helpdesk'),
)
