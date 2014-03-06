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
    'django_jenkins.tasks.run_jshint',
    'django_jenkins.tasks.run_pep8',
    'django_jenkins.tasks.run_pylint',
    'django_jenkins.tasks.run_sloccount',
    'django_jenkins.tasks.with_coverage',
)
# Note that SCSS linting is run directly from the jenkins script, since it
# is a different linter than standard csslint and requires options not
# supported by django-jenkins

PEP8_RCFILE = os.path.join(WORKSPACE_ROOT, '.pep8rc')
PYLINT_RCFILE = os.path.join(WORKSPACE_ROOT, '.pylintrc')

# TODO(sjdemartini): change static files directory structure to move third party
# JS into subdirectory, so that our own files can be in static/js, and others
# can be more easily distinguished. Then change the path below to be
# static/js/*.js to automatically lint all of (and only) our own files.
JSHINT_CHECKED_FILES = [
    os.path.join(WORKSPACE_ROOT, 'quark', 'static', 'js', 'main.js'),
    os.path.join(WORKSPACE_ROOT, 'quark', 'static', 'js', 'slideshow.js'),
    os.path.join(WORKSPACE_ROOT, 'quark', 'static', 'js', 'visual_datetime.js')
]


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
