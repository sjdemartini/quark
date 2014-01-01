from django.core.urlresolvers import reverse_lazy
from django.conf.urls import patterns
from django.conf.urls import url
from django.contrib.auth.views import login
from django.contrib.auth.views import logout
from django.contrib.auth.views import password_change
from django.contrib.auth.views import password_change_done

from quark.accounts.forms import PasswordChangeForm


app_name = 'accounts'


urlpatterns = patterns(
    '',
    url(r'^login/$', login,
        {'template_name': 'accounts/login.html',
         'current_app': app_name},
        name='login'),
    url(r'^logout/$', logout,
        # next_page is used to redirect to the root URL after logout if the
        # requested URL doesn't contain a redirect GET field
        {'next_page': '/',
         'template_name': 'accounts/logout.html',
         'current_app': app_name},
        name='logout'),
    url(r'change-password/$', password_change,
        {'template_name': 'accounts/change_password.html',
         'post_change_redirect': reverse_lazy('accounts:change-password-done'),
         'password_change_form': PasswordChangeForm,
         'current_app': app_name},
        name='change-password'),
    url(r'change-password/done/$', password_change_done,
        {'template_name': 'accounts/change_password_done.html',
         'current_app': app_name},
        name='change-password-done'),
)
