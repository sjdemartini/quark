#!/usr/bin/env python
import getpass
import subprocess
import sys


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


def run_command(command):
    return_code = subprocess.call(command, shell=True)
    if return_code != 0:
        print('Process failed.\n'
              'Failed command: ' + command)
        sys.exit(1)
    return True


def get_port(user, server_name):
    if server_name not in SERVER_PORTS:
        return None
    offset = OFFSETS.get(user, DEFAULT_OFFSET)
    port = SERVER_PORTS.get(server_name)
    port += offset
    if offset == DEFAULT_OFFSET:
        print('WARNING: Using shared port: %d' % port)
    print('Current IP and Port is: %s and %d' % (IP, port))
    return port


def run_server(server_name):
    port = get_port(getpass.getuser(), server_name)
    if not port:
        error_out()
    run_command('python manage.py syncdb')  # pick up changes to models
    run_command('python manage.py migrate')
    run_command('python manage.py collectstatic')
    run_command('python manage.py runserver %s:%d' % (IP, port))


def error_out():
    server_name_string = '|'.join(SERVER_PORTS.keys())
    print('Error: Script was incorrectly executed.\n'
          'Usage: ./dev {%s}' % server_name_string)
    sys.exit(1)


def main():
    if len(sys.argv) != 2:
        error_out()
    run_server(sys.argv[1])


if __name__ == '__main__':
    main()
