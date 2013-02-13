from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import TemplateView


admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', TemplateView.as_view(template_name='index.html'), name='index'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^courses/', include(
        'quark.courses.urls', app_name='courses', namespace='courses')),
    url(r'^email/', include(
        'quark.emailer.urls', app_name='emailer', namespace='emailer')),
    url(r'^minutes/', include(
        'quark.minutes.urls', app_name='minutes', namespace='minutes')),
    # TODO(mattchang): Get django-cms working for django-1.5
    #url(r'^', include('cms.urls')),
    url(r'^project-reports/', include('quark.project_reports.urls',
                                      namespace='project-reports')),
)

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
