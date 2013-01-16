import getpass

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from quark.utils.dev import DevServer
import quark.utils as dev_utils


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        if len(args) != 1:
            server_name_string = '|'.join(DevServer.PORTS.keys())
            raise CommandError(
                'Usage: python manage.py dev (%s)' % server_name_string)

        server = args[0]
        if server not in DevServer.PORTS.keys():
            raise CommandError('Invalid server name: "%s"' % server)

        dev_utils.update_db()
        dev = DevServer(username=getpass.getuser(), server=server)
        dev.run_server()
