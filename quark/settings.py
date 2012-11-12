# Django settings for quark project - TBP and PiE's merged project.

import getpass
import ldap
import os
import socket
import sys
import warnings

KEY_PATH = '/home/tbp/private'
if KEY_PATH not in sys.path:
    sys.path.append(KEY_PATH)
try:
    # pylint: disable-msg=F0401
    import quark_keys
except ImportError:
    print('Could not import quark_keys. Please make sure quark_keys.py exists '
          'on the path, and that there are no errors in the module.')
    sys.exit(1)


# Determine the path of your local workspace.
WORKSPACE_DJANGO_ROOT = os.path.abspath(
    os.path.dirname(globals()['__file__']))
WORKSPACE_ROOT = os.path.dirname(WORKSPACE_DJANGO_ROOT)

HOSTNAME = 'tbp.berkeley.edu'

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = ()

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        # We need this for per-user development databases.
        'NAME': 'quark_dev_%s' % getpass.getuser(),
        'USER': 'quark_dev',
        'PASSWORD': quark_keys.DEV_DB_PASSWORD,
    }
}

# Use 'app_label.model_name'
# Currently use django.contrib.auth.User.
# After Django 1.5, use custom user: quark.auth.QuarkUser
AUTH_USER_MODEL = 'auth.User'

AUTHENTICATION_BACKENDS = (
    'quark.qldap.backends.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
)

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Los_Angeles'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

LANGUAGES = [
    ('en', 'English'),
]

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

if USE_TZ:
    # Raise an error when dealing with timezone-unaware objects.
    warnings.filterwarnings(
        'error', r"DateTimeField received a naive datetime",
        RuntimeWarning, r'django\.db\.models\.fields')

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(WORKSPACE_ROOT, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(WORKSPACE_ROOT, 'static')

# URL prefix for static files.
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = quark_keys.SECRET_KEY

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

# This is for django-cms
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.request',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'cms.context_processors.media',
    'sekizai.context_processors.sekizai',
)

# This is for the django filer plugin
THUMBNAIL_PROCESSORS = (
    'easy_thumbnails.processors.colorspace',
    'easy_thumbnails.processors.autocrop',
    'filer.thumbnail_processors.scale_and_crop_with_subject_location',
    'easy_thumbnails.processors.filters',
)

MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'cms.middleware.page.CurrentPageMiddleware',
    'cms.middleware.user.CurrentUserMiddleware',
    'cms.middleware.toolbar.ToolbarMiddleware',
]

ROOT_URLCONF = 'quark.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'quark.wsgi.application'

TEMPLATE_DIRS = (
  os.path.join(WORKSPACE_DJANGO_ROOT, 'templates'),
)

CMS_TEMPLATES = (
    ('base.html', 'Base'),
)

# All projects that we write (and thus, need to be tested) should go here.
PROJECT_APPS = [
    'quark.auth',
    'quark.base',
    'quark.qldap',
    'quark.utils',
]

# Third-party apps belong here, since we won't use them for testing.
THIRD_PARTY_APPS = [
    'cms',
    'cms.plugins.link',
    'cms.plugins.snippet',
    'cms.plugins.text',
    'cmsplugin_filer_file',
    'cmsplugin_filer_folder',
    'cmsplugin_filer_image',
    'cmsplugin_filer_video',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django_jenkins',
    'easy_thumbnails',
    'filer',
    'menus',
    'mptt',
    'reversion',
    'sekizai',
    'south',
]

# This is the actual variable that django looks at.
INSTALLED_APPS = PROJECT_APPS + THIRD_PARTY_APPS

DEFAULT_FROM_EMAIL = 'webmaster@' + HOSTNAME

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

# YouTube Secret Stuff
YT_USERNAME = 'BerkeleyTBP'
YT_PRODUCT = 'noiro'
YT_DEVELOPER_KEY = quark_keys.YT_DEVELOPER_KEY
YT_PASSWORD = quark_keys.YT_PASSWORD

# http://www.djangosnippets.org/snippets/1653/
RECAPTCHA_PRIVATE_KEY = quark_keys.RECAPTCHA_PRIVATE_KEY
RECAPTCHA_PUBLIC_KEY = quark_keys.RECAPTCHA_PUBLIC_KEY

# LDAP settings
LDAP = {
    'HOST': 'ldap://localhost',
    'BASE': 'dc=tbp,dc=berkeley,dc=edu',
    'SCOPE': ldap.SCOPE_SUBTREE,
}
LDAP_BASE = {
    'PEOPLE': 'ou=People,' + LDAP['BASE'],
    'GROUP': 'ou=Group,' + LDAP['BASE'],
    'DN': 'uid=ldapwriter,ou=System,' + LDAP['BASE'],
    'PASSWORD': quark_keys.LDAP_BASEDN_PASSWORD,
}
LDAP_GROUPS = {
    'TBP': ['tbp-officers', 'tbp-members', 'tbp-candidates'],
    'PIE': ['pie-mentors', 'pie-it', 'pie-staff', 'pie-students',
            'pie-teachers'],
}
LDAP_DEFAULT_USER = 'uid=default,ou=System,' + LDAP['BASE']

# LDAP and CustomUser (QuarkUser) valid username regex
# Please use raw string notation (i.e. r'text') to keep regex sane.
# Update quark/qldap/tests.py: test_valid_username_regex() to match
VALID_USERNAME = r'^[a-z][a-z0-9]{2,29}$'
USERNAME_HELPTEXT = ('Username must be 3-30 character, start with a letter,'
                     ' and use only lowercase letters and numbers.')

# Jenkins integration.
JENKINS_TASKS = (
    'django_jenkins.tasks.django_tests',
    'django_jenkins.tasks.run_csslint',
    'django_jenkins.tasks.run_jslint',
    'django_jenkins.tasks.run_pep8',
    'django_jenkins.tasks.run_pylint',
    'django_jenkins.tasks.run_sloccount',
    'django_jenkins.tasks.with_coverage',
)
PYLINT_RCFILE = os.path.join(WORKSPACE_ROOT, '.pylintrc')

# Valid types are 'semester' and 'quarter'.
TERM_TYPE = 'semester'

###############################################################################
# Import any local settings to override default settings.
###############################################################################
try:
    # pylint: disable-msg=F0401
    from settings_local import *
except ImportError:
    # If the file doesn't exist, print a warning message but do not fail.
    print('WARNING: No settings_local file was detected.')
###############################################################################
# End local settings section.
###############################################################################

# separate cookies for dev server, dev-tbp, and production
SESSION_COOKIE_NAME = '%s_sessionid' % socket.gethostname().split('.')[0]
if DEBUG:
    SESSION_COOKIE_NAME = 'dbg_' + SESSION_COOKIE_NAME
