from django.conf.urls import patterns
from django.conf.urls import url
from django.contrib.auth.views import login
from django.contrib.auth.views import logout


urlpatterns = patterns(
    '',
    url(r'^login/$', login, {'template_name': 'accounts/login.html'},
        name='login'),
    url(r'^logout/$', logout,
        # next_page is used to redirect to the root URL after logout if the
        # requested URL doesn't contain a redirect GET field
        {'next_page': '/', 'template_name': 'accounts/logout.html'},
        name='logout'),
)
