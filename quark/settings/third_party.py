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
