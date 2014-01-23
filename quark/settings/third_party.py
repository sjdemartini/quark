"""Settings for 3rd Party Apps used by Quark"""
import os
import sys

from quark.settings.base import WORKSPACE_ROOT


# Mailman path
MMPATH = '/usr/lib/mailman'
if MMPATH not in sys.path:
    sys.path.append(MMPATH)


# Set up SASS (SCSS) compression for django-compressor
COMPRESS_PRECOMPILERS = (
    ('text/x-scss', 'sass {infile}:{outfile}'),
)

# Use the "AbsoluteFilter" to change relative URLs to absolute URLs, and
# CSSMinFilter to minify the CSS
COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.CSSMinFilter'
]

# Make django-compressor store its output compressed files in the original
# location of the static files, rather than a subfolder
COMPRESS_OUTPUT_DIR = ''


# Jenkins integration.
JENKINS_TASKS = (
    'django_jenkins.tasks.django_tests',
    'django_jenkins.tasks.run_csslint',
    # TODO(wli): re-enable jshint when it stops crashing.
    # 'django_jenkins.tasks.run_jshint',
    'django_jenkins.tasks.run_pep8',
    'django_jenkins.tasks.run_pylint',
    'django_jenkins.tasks.run_sloccount',
    'django_jenkins.tasks.with_coverage',
)

PYLINT_RCFILE = os.path.join(WORKSPACE_ROOT, '.pylintrc')


# Set up aliases for easy-thumbnails
THUMBNAIL_ALIASES = {
    '': {
        'avatar': {
            'size': (40, 40),
            'autocrop': True,
            'crop': 'smart'
        },
        'officericon': {
            'size': (150, 150),
            'autocrop': True,
            'crop': 'smart',
            'quality': 90
        }
    },
}


# Define the function that determines whether the Django Debug Toolbar should
# be shown
def show_toolbar(request):
    """Return True so that the Django Debug Toolbar is always shown.

    This function should only be used with dev!

    By default, the Debug Toolbar would only be shown when DEBUG=True and the
    request is from an IP listed in the INTERNAL_IPS setting.
    """
    return True
