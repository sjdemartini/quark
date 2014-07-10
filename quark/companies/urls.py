from django.conf.urls import patterns
from django.conf.urls import url

from quark.companies.views import CompanyCreateView
from quark.companies.views import CompanyDetailView
from quark.companies.views import CompanyEditView
from quark.companies.views import CompanyListView
from quark.companies.views import CompanyRepCreateView
from quark.companies.views import CompanyRepDeleteView
from quark.companies.views import ResumeListView


urlpatterns = patterns(
    '',
    url(r'^companies/$', CompanyListView.as_view(), name='list'),
    url(r'^companies/(?P<company_pk>\d+)/$', CompanyDetailView.as_view(),
        name='company-detail'),
    url(r'^companies/create/$', CompanyCreateView.as_view(),
        name='company-create'),
    url(r'^companies/edit/(?P<company_pk>\d+)/$', CompanyEditView.as_view(),
        name='company-edit'),
    url(r'^companies/rep-create/$', CompanyRepCreateView.as_view(),
        name='rep-create'),
    url(r'^companies/rep-delete/(?P<rep_pk>\d+)/$',
        CompanyRepDeleteView.as_view(), name='rep-delete'),
    url(r'^resumes/$', ResumeListView.as_view(),
        name='resumes'),

    # TODO(sjdemartini): Add views for companies to manage their own contact
    # information and company info (e.g., website and logo)
)
