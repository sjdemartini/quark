from django.core.management import execute_from_command_line


class DevServer(object):
    DEFAULT_IP = '0.0.0.0'
    PORTS = {
        'tbp': 8000,
        'pie': 9000,
    }
    DEFAULT_OFFSET = 999

    # The value for this dict is the port and should be a number between 80 and
    # 998 To add a new person and port: add the username and port into the dict
    # Please pick the next available number. These numbers are increased by
    # 8000 if using the tbp server or 9000 for pie
    OFFSETS = {
        'wli': 80,
        'flieee': 85,
        'andrewlee': 88,
        'christandiono': 95,
        'wangj': 97,
        'amyfu': 98,
        'wesleyahunt': 99,
        'giovanni': 100,
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
        'tywade': 148,
        'nitishp': 421,
        'akakitani': 765,
        'ericdwang': 888,
        # Please do not use port 999 since it is the shared port
    }

    def __init__(self, username=None, server='tbp', localhost=False):
        # pylint: disable=C0103
        self.ip = 'localhost' if localhost else DevServer.DEFAULT_IP
        self.port = self.get_port(username, server)

    def get_port(self, username, server_name, verbose=True):
        """
        Given a username, and server name (Currently tbp or pie), returns the
        corresponding port number using a dictionary lookup. If the look up
        fails, returns a shared port. The port is also set as the current port
        for the object instance.
        """
        if server_name not in DevServer.PORTS:
            raise KeyError('Invalid server name: "%s"' % server_name)
        offset = DevServer.OFFSETS.get(username, DevServer.DEFAULT_OFFSET)
        self.port = DevServer.PORTS.get(server_name)
        self.port += offset
        if verbose:
            if offset == DevServer.DEFAULT_OFFSET:
                print('WARNING: Using shared port: %d' % self.port)
            print('Current IP and Port is: %s and %d' % (self.ip, self.port))
        return self.port

    def run_server(self, verbose=True):
        """Runs a dev server based on current settings"""
        if verbose:
            print('Running server...')
        try:
            execute_from_command_line(
                ['manage.py', 'runserver', '%s:%d' % (self.ip, self.port)])
        except KeyboardInterrupt:
            # Catch Ctrl-C and exit cleanly without a stacktrace
            if verbose:
                print('KeyboardInterrupt: Exiting')
