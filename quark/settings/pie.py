# python: disable=W0614,W0401
from quark.settings.base import *


# TODO(flieee): dynamic SITE_ID working so pie doesn't need separate settings
HOSTNAME = 'pioneers.berkeley.edu'

ALLOWED_HOSTS = [HOSTNAME]

DEFAULT_FROM_EMAIL = 'webmaster@' + HOSTNAME
SERVER_EMAIL = DEFAULT_FROM_EMAIL

SITE_NAME = 'pie'
SITE_ID = 4

# Import any local settings
try:
    # python: disable=F0401,W0401,W0614
    from quark.settings_local import *
except ImportError:
    # Don't bug me if there's no local settings.
    pass
