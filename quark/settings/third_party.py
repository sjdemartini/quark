"""Settings for 3rd Party Apps used by Quark"""
import os

from quark.settings.base import WORKSPACE_ROOT


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


# Define the function that determines whether the Django Debug Toolbar should
# be shown
def show_toolbar(request):
    """Return True so that the Django Debug Toolbar is always shown.

    This function should only be used with dev!

    By default, the Debug Toolbar would only be shown when DEBUG=True and the
    request is from an IP listed in the INTERNAL_IPS setting.
    """
    return True
