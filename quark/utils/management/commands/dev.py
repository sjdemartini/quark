import getpass

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from quark.utils.dev import DevServer
import quark.utils as dev_utils


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # Don't need args anymore with SITE_NAME setting
        if len(args) != 0:
            raise CommandError('Usage: python manage.py dev')

        server = settings.SITE_NAME
        if server not in DevServer.PORTS.keys():
            valid_servers = '|'.join(DevServer.PORTS.keys())
            raise ImproperlyConfigured('Invalid server name "%s" (%s)' % (
                server, valid_servers))

        print('Running development server for "%s"' % server)
        dev_utils.update_db()
        dev = DevServer(username=getpass.getuser(), server=server)
        dev.run_server()
