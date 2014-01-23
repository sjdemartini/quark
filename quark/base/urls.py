from django.conf.urls import patterns
from django.conf.urls import url

from quark.base.views import OfficersView

urlpatterns = patterns(
    '',
    url(r'^$', OfficersView.as_view(), name='officers'),
)
