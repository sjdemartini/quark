from django.conf.urls import patterns
from django.conf.urls import url

from quark.base.views import HomePageView
from quark.base.views import ITToolsView
from quark.base.views import OfficersListView
from quark.base.views import OfficerPortalView
from quark.base.views import ProcrastinationView


urlpatterns = patterns(
    '',
    url(r'^$', HomePageView.as_view(), name='home'),
    url(r'^officers/$', OfficersListView.as_view(), name='officers'),
    # TODO(sjdemartini): Restrict the pages below with proper permissions
    url(r'^officer-portal/$', OfficerPortalView.as_view(),
        name='officer-portal'),
    url(r'^it-tools/$', ITToolsView.as_view(), name='it-tools'),
    url(r'^procrastination/$', ProcrastinationView.as_view(),
        name='procrastination'),
    # TODO(sjdemartini): Add a Members database view
)
