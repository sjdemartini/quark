from django.conf.urls import patterns
from django.conf.urls import url

from quark.companies.views import CompanyDetailView
from quark.companies.views import CompanyListView
from quark.companies.views import CompanyRepCreateView


urlpatterns = patterns(
    '',
    url(r'^companies/$', CompanyListView.as_view(), name='list'),
    url(r'^companies/(?P<company_pk>\d+)/$', CompanyDetailView.as_view(),
        name='detail'),
    url(r'^companies/create-rep/$', CompanyRepCreateView.as_view(),
        name='create-rep')

    # TODO(sjdemartini): Add views for creating new companies, for companies to
    # manage their own contact information and company info (e.g., website and
    # logo)
)
