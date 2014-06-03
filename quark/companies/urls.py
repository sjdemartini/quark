from django.conf.urls import patterns
from django.conf.urls import url

from quark.companies.views import CompanyCreateView
from quark.companies.views import CompanyDetailView
from quark.companies.views import CompanyListView
from quark.companies.views import CompanyRepCreateView
from quark.companies.views import ResumeListView


urlpatterns = patterns(
    '',
    url(r'^companies/$', CompanyListView.as_view(), name='list'),
    url(r'^companies/(?P<company_pk>\d+)/$', CompanyDetailView.as_view(),
        name='company-detail'),
    url(r'^companies/create/$', CompanyCreateView.as_view(),
        name='create-company'),
    url(r'^companies/create-rep/$', CompanyRepCreateView.as_view(),
        name='create-rep'),
    url(r'^resumes/$', ResumeListView.as_view(),
        name='resumes'),

    # TODO(sjdemartini): Add views for companies to manage their own contact
    # information and company info (e.g., website and logo)
)
