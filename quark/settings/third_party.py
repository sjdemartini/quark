"""Settings for 3rd Party Apps used by Quark"""
import os

from quark.settings.base import WORKSPACE_ROOT


# django-cms settings
# Adds 2 new date-time fields in the advanced-settings tab of the page.
# Allows for limiting the time a page is published.
CMS_SHOW_START_DATE = True
CMS_SHOW_END_DATE = True

# Disables CMS permissions to be given on a per page basis
CMS_PERMISSION = False

# URL base for CMS's media files
CMS_MEDIA_URL = '/cms/'

# List of templates you can select for a page
CMS_TEMPLATES = (
    ('base.html', 'Base'),
)

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


