import getpass
import os

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from quark.utils.dev import DevServer
import quark.utils as dev_utils


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        if len(args) != 0:
            # Don't need any args
            raise CommandError('Usage: python manage.py dev')

        if os.environ.get('RUN_MAIN', False) == 'true':
            # Only run update_db if this is not a thread spawned by
            # restart_with_reloader. This prevents update_db from happening
            # more than once when the management command is run. See
            # https://code.djangoproject.com/ticket/8085#comment:13
            print 'Running development server'
            dev_utils.update_db()

        dev = DevServer(username=getpass.getuser())
        dev.run_server()
