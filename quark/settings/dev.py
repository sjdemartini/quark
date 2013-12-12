import getpass
import subprocess

from quark.settings.base import WORKSPACE_ROOT
# pylint: disable=F0401
import quark_keys


###############################################################################
# Private Variables for this dev instance
###############################################################################
_user = getpass.getuser()
_git_cmd = ['git', '--git-dir=%s/.git' % WORKSPACE_ROOT,
            '--work-tree=%s' % WORKSPACE_ROOT]
try:
    # Get dev user contact info from git
    _name = subprocess.check_output(
        _git_cmd + ['config', 'user.name']).strip()
    _email = subprocess.check_output(
        _git_cmd + ['config', 'user.email']).strip()
except subprocess.CalledProcessError:
    _name = 'Test'
    _email = 'test@tbp.berkeley.edu'


###############################################################################
# Override settings for all dev instances
###############################################################################
DEBUG = True
TEMPLATE_DEBUG = DEBUG

# Set dev user's info for admins/manager
ADMINS = ((_name, _email),)
MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        # We need this for per-user development databases.
        'NAME': 'quark_dev_%s' % _user,
        'USER': 'quark_dev',
        'PASSWORD': quark_keys.DEV_DB_PASSWORD,
    }
}

# Custom dev cookie session ID
SESSION_COOKIE_NAME =  'quark_dev_%s_sid' % _user

# Always show the Django Debug Toolbar on dev. By default, the Debug Toolbar
# would only be shown when DEBUG=True and the request is from an IP listed in
# the INTERNAL_IPS setting.
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: True
}

# Use nginx proxy. Dev server available at https://tbp.berkeley.edu/PORT/
# Set this config value in your settings_local.py file if you want to use to
# be more secure (yes, you do) and use a HTTPS proxy instead of
# http://tbp.berkeley.edu:PORT/
#FORCE_SCRIPT_NAME = '/%d' % <Your Port Here>
