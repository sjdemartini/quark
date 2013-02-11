# python: disable=W0401,W0614
from quark.settings.base import *


HOSTNAME = 'tbp.berkeley.edu'

DEFAULT_FROM_EMAIL = 'webmaster@' + HOSTNAME
SERVER_EMAIL = DEFAULT_FROM_EMAIL

SITE_NAME = 'tbp'
SITE_ID = 2

# Import any local settings
try:
    # pylint: disable=F0401,W0401,W0614
    from quark.settings_local import *
except ImportError:
    # Don't bug me if there's no local settings.
    pass
