from django.core.urlresolvers import reverse_lazy
from django.conf.urls import patterns
from django.conf.urls import url
from django.contrib.auth.views import login
from django.contrib.auth.views import logout
from django.contrib.auth.views import password_change
from django.contrib.auth.views import password_change_done
from django.contrib.auth.views import password_reset
from django.contrib.auth.views import password_reset_complete
from django.contrib.auth.views import password_reset_confirm
from django.contrib.auth.views import password_reset_done

from quark.accounts.forms import AuthenticationForm
from quark.accounts.forms import PasswordChangeForm
from quark.accounts.forms import PasswordResetForm
from quark.accounts.forms import SetPasswordForm


app_name = 'accounts'


urlpatterns = patterns(
    '',
    url(r'^login/$', login,
        {'template_name': 'accounts/login.html',
         'authentication_form': AuthenticationForm,
         'current_app': app_name},
        name='login'),
    url(r'^logout/$', logout,
        # next_page is used to redirect to the root URL after logout if the
        # requested URL doesn't contain a redirect GET field
        {'next_page': reverse_lazy('home'),
         'template_name': 'accounts/logout.html',
         'current_app': app_name},
        name='logout'),

    # Changing password (change, then done):
    url(r'password/change/$', password_change,
        {'template_name': 'accounts/password_change.html',
         'post_change_redirect': reverse_lazy('accounts:password-change-done'),
         'password_change_form': PasswordChangeForm,
         'current_app': app_name},
        name='password-change'),
    url(r'password/change/done/$', password_change_done,
        {'template_name': 'accounts/password_change_done.html',
         'current_app': app_name},
        name='password-change-done'),

    # Resetting password (reset, then sent, then confirm, then done):
    url(r'password/reset/$', password_reset,
        {'template_name': 'accounts/password_reset.html',
         'email_template_name': 'accounts/password_reset_email.html',
         'password_reset_form': PasswordResetForm,
         'post_reset_redirect': reverse_lazy('accounts:password-reset-sent'),
         'current_app': app_name},
        name='password-reset'),
    url(r'password/reset/sent/$', password_reset_done,
        {'template_name': 'accounts/password_reset_sent.html',
         'current_app': app_name},
        name='password-reset-sent'),
    # URL regex for uid and token copied from Django source
    url((r'^password/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/'
         '(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$'),
        password_reset_confirm,
        {'template_name': 'accounts/password_reset_confirm.html',
         'set_password_form': SetPasswordForm,
         'post_reset_redirect': reverse_lazy(
             'accounts:password-reset-complete'),
         'current_app': app_name},
        name='password-reset-confirm'),
    url(r'^password/reset/complete/', password_reset_complete,
        {'template_name': 'accounts/password_reset_complete.html',
         'current_app': app_name},
        name='password-reset-complete'),
)
