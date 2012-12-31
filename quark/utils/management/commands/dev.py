import getpass
import glob

from django.core.management import execute_from_command_line
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.conf import settings


IP = '0.0.0.0'
SERVER_PORTS = {
    'tbp': 8000,
    'pie': 9000,
}
DEFAULT_OFFSET = 999


# The value for this dict is the port and should be a number between 80 and 998
# To add a new person and port: add the username and port into the dict
# Please pick the next available number
# These numbers are increased by 8000 if using the tbp server or 9000 for pie
OFFSETS = {
    'wli': 80,
    'flieee': 85,
    'andrewlee': 88,
    'christandiono': 95,
    'wangj': 97,
    'amyfu': 98,
    'wesleyahunt': 99,
    'exiao': 134,
    'mattchang': 136,
    'bcortright': 137,
    'tonydear': 138,
    'peterchen': 139,
    'jeffkysun': 141,
    'sjdemartini': 144,
    'lauph': 145,
    'orweizman': 146,
    'tristanj': 147,
    # Please do not use port 999 since it is the shared port
}


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        if len(args) != 1:
            server_name_string = '|'.join(SERVER_PORTS.keys())
            raise CommandError(
                'Usage: python manage.py dev {%s}' % server_name_string)

        port = self.get_port(getpass.getuser(), args[0])

        # pick up changes to models
        print('Running syncdb...')
        execute_from_command_line(['manage.py', 'syncdb'])

        print('Loading initial data...')
        self.load_initial_data()

        print('Running any migrations...')
        execute_from_command_line(['manage.py', 'migrate'])

        print('Collecting static files...')
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])

        print('Running server...')
        try:
            execute_from_command_line(
                ['manage.py', 'runserver', '%s:%d' % (IP, port)])
        except KeyboardInterrupt:
            # Catch Ctrl-C and exit cleanly without a stacktrace
            print('KeyboardInterrupt: Exiting')

    def get_port(self, user, server_name):
        if server_name not in SERVER_PORTS:
            raise CommandError('Invalid server name: `%s`' % server_name)
        offset = OFFSETS.get(user, DEFAULT_OFFSET)
        port = SERVER_PORTS.get(server_name)
        port += offset
        if offset == DEFAULT_OFFSET:
            print('WARNING: Using shared port: %d' % port)
        print('Current IP and Port is: %s and %d' % (IP, port))
        return port

    def load_initial_data(self):
        # We only load yaml fixtures. Python can't handle {} in globs
        imports = []
        for project in settings.PROJECT_APPS:
            imports += glob.glob('/'.join(
                [settings.WORKSPACE_ROOT] + project.split('.') +
                ['fixtures', '*.yaml']))
        if imports:
            execute_from_command_line(['manage.py', 'loaddata'] + imports)
