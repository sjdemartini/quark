from django.conf import settings


def local_env(request):
    """Add a context variable indicating whether the local environment is
    development, staging, or production, and a second variable indicating
    whether DEBUG mode is active.

    The LOCAL_ENV variable should be equal to one of 'dev', 'staging', or
    'production'. The debug variable is a boolean.
    """
    return {
        'LOCAL_ENV': settings.LOCAL_ENV,
        'debug': settings.DEBUG
    }
