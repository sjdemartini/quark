from django.conf.urls import patterns
from django.conf.urls import url
from django.views.generic import TemplateView

from quark.base.views import HomePageView
from quark.base.views import OfficersListView


urlpatterns = patterns(
    '',
    url(r'^$', HomePageView.as_view(), name='home'),
    url(r'^officers/$', OfficersListView.as_view(), name='officers'),
    # TODO(sjdemartini): Restrict the pages below with proper permissions
    url(r'^officer-portal/$', TemplateView.as_view(
        template_name='base/officer_portal.html'), name='officer-portal'),
    url(r'^it-tools/$', TemplateView.as_view(
        template_name='base/it_tools.html'), name='it-tools'),
    url(r'^procrastination/$', TemplateView.as_view(
        template_name='base/procrastination.html'), name='procrastination'),
    # TODO(sjdemartini): Add a Members database view
)
