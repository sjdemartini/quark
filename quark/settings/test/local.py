"""Default settings for running tests via jenkins locally."""

# pylint: disable=W0401,W0614
from quark.settings.test import *

# Only enable jenkins tasks that are necessary for passing a build (exclude
# code coverage, etc.)
JENKINS_TASKS = (
    #'django_jenkins.tasks.run_csslint',
    'django_jenkins.tasks.run_jshint',
    'django_jenkins.tasks.run_pep8',
    'django_jenkins.tasks.run_pylint',
)
