import glob

from django.conf import settings
from django.core.management import execute_from_command_line
from south import migration

from quark.settings import PROJECT_APPS


def update_db(verbose=True):
    """Prepare and update the current database.

    Prepare schema migrations, sync the database, run migrations, load data
    from fixtures, and collect static files.

    The South schema migrations are prepared before the syncdb commands so that
    new apps will be managed by South. syncdb is run before running the
    actual migrations so that the non-South apps can be added to and synced in
    the database first (such as Django's auth app, and other apps upon which
    South apps might depend). syncdb will be a no-op for the apps under South
    management.
    """
    # South migrations should be prepared before syncdb
    if verbose:
        print('Preparing South migrations...')
    prepare_migrations()

    # Pick up changes to models not managed by South, or initialize the
    # database if it hasn't been before
    if verbose:
        print('Running syncdb...')
    execute_from_command_line(['manage.py', 'syncdb'])

    # Perform any migrations on new apps
    if verbose:
        print('Running any migrations...')
    execute_from_command_line(['manage.py', 'migrate'])

    if verbose:
        print('Loading initial data...')
    load_initial_data()

    if verbose:
        print('Collecting static files...')
    execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])


def prepare_migrations():
    """Use South to prepare any schema migrations for new project apps.

    This ensures that any newly-created apps are set to be managed by South.

    If a schema change is made at a later time, a schema migration should be
    set up manually. Usually it is as simple as:
    manage.py schemamigration --auto <app name>
    The South API should be referenced for anything that requires more complex
    migration: http://south.readthedocs.org/en/latest/
    """
    # Apps that should NOT be managed by South:
    # (Note that a Django custom user model cannot be managed by South:
    # http://south.aeracode.org/ticket/1179)
    # quark.accounts - excluded since only contains a proxy model for the
    #                  Django auth.User
    excluded_apps = set(['quark.accounts'])

    # Get a list of all apps that are "migrated" (that is, managed by South).
    # The full_name() method returns a string the app name but includes
    # '.migrations', so remove that from the end of the string with slicing.
    migrated_apps = set([app_mig.full_name()[:-11]
                         for app_mig in migration.all_migrations()])

    # Add all project apps to be migrated, if not already managed by South:
    for app in PROJECT_APPS:
        if app not in excluded_apps and app not in migrated_apps:
            # Perform an initial migration
            execute_from_command_line(
                ['manage.py', 'schemamigration', '--initial', app])


def load_initial_data():
    # We only load yaml fixtures. Python can't handle {} in globs
    imports = []
    for project in settings.PROJECT_APPS:
        imports += glob.glob('/'.join(
            [settings.WORKSPACE_ROOT] + project.split('.') +
            ['fixtures', '*.yaml']))
    if imports:
        execute_from_command_line(['manage.py', 'loaddata'] + imports)
