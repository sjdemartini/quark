from django.conf.urls import patterns
from django.conf.urls import url

from quark.candidates.views import CandidateEditView
from quark.candidates.views import CandidateListView
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
    url(r'^requirements/$',
        CandidateRequirementsEditView.as_view(), name='edit-requirements'),
    url(r'^requirements/add/(?P<req_type>\w+)/$',
        CandidateRequirementCreateView.as_view(), name='add-requirement'),
    url(r'^requirements/(?P<req_pk>\d+)/delete/$',
        CandidateRequirementDeleteView.as_view(), name='delete-requirement'),
    url(r'^(?P<candidate_pk>\d+)/challenge/(?P<challenge_pk>\d+)/$',
        ChallengeVerifyView.as_view(), name='verify-challenge'),
)
