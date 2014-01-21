import getpass

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from quark.utils.dev import DevServer
import quark.utils as dev_utils


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        if len(args) != 0:
            # Don't need any args
            raise CommandError('Usage: python manage.py dev')

        print 'Running development server'
        dev_utils.update_db()
        dev = DevServer(username=getpass.getuser())
        dev.run_server()
