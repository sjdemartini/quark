from django.conf import settings
from django.conf.urls import include
from django.conf.urls import patterns
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


admin.autodiscover()


urlpatterns = patterns(
    '',
    url(r'^', include('quark.base.urls',
                      app_name='base')),
    url(r'^accounts/', include('quark.accounts.urls',
                               app_name='accounts',
                               namespace='accounts')),
    url(r'^achievements/', include('quark.achievements.urls',
                                   app_name='achievements',
                                   namespace='achievements')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^candidates/', include('quark.candidates.urls',
                                 app_name='candidates',
                                 namespace='candidates')),
    url(r'^courses/', include('quark.courses.urls',
                              app_name='courses',
                              namespace='courses')),
    url(r'^email/', include('quark.emailer.urls',
                            app_name='emailer',
                            namespace='emailer')),
    url(r'^events/', include('quark.events.urls',
                             app_name='events',
                             namespace='events')),
    url(r'^exams/', include('quark.exams.urls',
                            app_name='exams',
                            namespace='exams')),
    url(r'^industry/', include('quark.companies.urls',
                               app_name='companies',
                               namespace='companies')),
    url(r'^mailing-lists/', include('quark.mailing_lists.urls',
                                    app_name='mailing_lists',
                                    namespace='mailing-lists')),
    url(r'^minutes/', include('quark.minutes.urls',
                              app_name='minutes',
                              namespace='minutes')),
    url(r'^newsreel/', include('quark.newsreel.urls',
                               app_name='newsreel',
                               namespace='newsreel')),
    url(r'^notifications/', include('quark.notifications.urls',
                                    app_name='notifications',
                                    namespace='notifications')),
    url(r'^past-presidents/', include('quark.past_presidents.urls',
                                      app_name='past_presidents',
                                      namespace='past-presidents')),
    url(r'^profile/', include('quark.user_profiles.urls',
                              app_name='user_profiles',
                              namespace='user-profiles')),
    url(r'^project-reports/', include('quark.project_reports.urls',
                                      app_name='project_reports',
                                      namespace='project-reports')),
    url(r'^quote-board/', include('quark.quote_board.urls',
                                  app_name='quote_board',
                                  namespace='quote-board')),
    url(r'^resumes/', include('quark.resumes.urls',
                              app_name='resumes',
                              namespace='resumes')),
    url(r'^vote/', include('quark.vote.urls',
                           app_name='vote',
                           namespace='vote')),
)

# Add flatpages URLs
urlpatterns += patterns(
    'django.contrib.flatpages.views',
    url(r'^about/$', 'flatpage', {'url': '/about/'}, name='about'),
    url(r'^about/contact/$', 'flatpage', {'url': '/about/contact/'},
        name='contact'),
    url(r'^about/eligibility/$', 'flatpage', {'url': '/about/eligibility/'},
        name='eligibility'),
    url(r'^industry/$', 'flatpage', {'url': '/industry/'}, name='industry'),
    url(r'^people/committees/$', 'flatpage', {'url': '/people/committees/'},
        name='committees'),
    url(r'^student-resources/$', 'flatpage', {'url': '/student-resources/'},
        name='student-resources'),
)

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
