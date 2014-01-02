# python: disable=W0401,W0614
from quark.settings.base import *


HOSTNAME = 'tbp.berkeley.edu'

ALLOWED_HOSTS = [HOSTNAME]

DEFAULT_FROM_EMAIL = 'webmaster@' + HOSTNAME
SERVER_EMAIL = DEFAULT_FROM_EMAIL

SITE_NAME = 'tbp'
SITE_ID = 2
