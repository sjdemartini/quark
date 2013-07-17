from django.conf.urls import patterns
from django.conf.urls import url

from quark.candidates.views import CandidateEditView
from quark.candidates.views import CandidateListView
from quark.candidates.views import CandidatePhotoView
from quark.candidates.views import CandidatePortalView
from quark.candidates.views import CandidateRequirementCreateView
from quark.candidates.views import CandidateRequirementDeleteView
from quark.candidates.views import CandidateRequirementsEditView
from quark.candidates.views import ChallengeVerifyView


urlpatterns = patterns(
    '',
    url(r'^$', CandidateListView.as_view(), name='list-current'),
    url(r'^(?P<term>\w{2}\d{4})/$', CandidateListView.as_view(), name='term'),
    url(r'^(?P<candidate_pk>\d+)/$', CandidateEditView.as_view(),
        name='edit'),
    url(r'^(?P<candidate_pk>\d+)/photo$', CandidatePhotoView.as_view(),
        name='photo'),
    url(r'^requirements/$',
        CandidateRequirementsEditView.as_view(), name='edit-requirements'),
    url(r'^requirements/add/(?P<req_type>\w+)/$',
        CandidateRequirementCreateView.as_view(), name='add-requirement'),
    url(r'^requirements/(?P<req_pk>\d+)/delete/$',
        CandidateRequirementDeleteView.as_view(), name='delete-requirement'),
    url(r'^challenges/$', ChallengeVerifyView.as_view(), name='challenges'),
    url(r'^portal/$', CandidatePortalView.as_view(), name='portal'),
)