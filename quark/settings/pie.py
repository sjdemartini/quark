from quark.settings.base import *


# TODO(flieee): dynamic SITE_ID working so pie doesn't need separate settings
HOSTNAME = 'pioneers.berkeley.edu'

DEFAULT_FROM_EMAIL = 'webmaster@' + HOSTNAME
SERVER_EMAIL = DEFAULT_FROM_EMAIL

SITE_NAME = 'pie'
SITE_ID = 4

# Import any local settings
try:
    # pylint: disable=F0401
    from quark.settings_local import *
except ImportError:
    # Don't bug me if there's no local settings.
    pass
