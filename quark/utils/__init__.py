import glob

from django.conf import settings
from django.core.management import execute_from_command_line


def update_db(verbose=True):
    if verbose:
        print 'Running syncdb...'
    execute_from_command_line(['manage.py', 'syncdb'])

    if verbose:
        print 'Running any migrations...'
    execute_from_command_line(['manage.py', 'migrate'])

    if verbose:
        print 'Loading initial data...'
    load_initial_data()


def load_initial_data():
    # We only load yaml fixtures. Python can't handle {} in globs
    imports = []
    for project in settings.PROJECT_APPS:
        imports += glob.glob('/'.join(
            [settings.WORKSPACE_ROOT] + project.split('.') +
            ['fixtures', '*.yaml']))
    if imports:
        execute_from_command_line(['manage.py', 'loaddata'] + imports)
