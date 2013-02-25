from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^courses/', include(
        'quark.courses.urls', app_name='courses', namespace='courses')),
    url(r'^email/', include(
        'quark.emailer.urls', app_name='emailer', namespace='emailer')),
    # TODO(mattchang): Get django-cms working for django-1.5
    #url(r'^', include('cms.urls')),
)

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
