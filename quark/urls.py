from django.conf import settings
from django.conf.urls import include
from django.conf.urls import patterns
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import TemplateView

from quark.base.views import HomePageView


admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', HomePageView.as_view(), name='home'),
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
    url(r'^mailing-lists/', include('quark.mailing_lists.urls',
                                    app_name='mailing_lists',
                                    namespace='mailing-lists')),
    url(r'^minutes/', include('quark.minutes.urls',
                              app_name='minutes',
                              namespace='minutes')),
    url(r'^newsreel/', include('quark.newsreel.urls',
                               app_name='newsreel',
                               namespace='newsreel')),
    url(r'^officers/', include('quark.base.urls',
                               app_name='officers',
                               namespace='officers')),
    url(r'^past-presidents/', include('quark.past_presidents.urls',
                                      app_name='past_presidents',
                                      namespace='past-presidents')),
    url(r'^profile/', include('quark.user_profiles.urls',
                              app_name='user_profiles',
                              namespace='user-profiles')),
    url(r'^project-reports/', include('quark.project_reports.urls',
                                      app_name='project_reports',
                                      namespace='project-reports')),
    url(r'^resume/', include('quark.resumes.urls',
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
    url(r'^contact/$', 'flatpage', {'url': '/contact/'}, name='contact'),
    url(r'^industry/$', 'flatpage', {'url': '/industry/'}, name='industry'),
)

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
