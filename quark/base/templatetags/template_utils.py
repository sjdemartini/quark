from django import template
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.http import urlencode

from quark.accounts.models import APIKey


register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Allow dictionary lookups with a variable as the key in templates.

    Usage in templates:
    {% load template_utils %}
    {{ mydict|get_item:var_name }}

    This is equivalent to doing mydict[var_name] in Python.
    """
    return dictionary.get(key)


@register.simple_tag(takes_context=True)
def modify_query_params(context, **kwargs):
    """
    Modify query parameters for the current URL.

    Takes the current GET parameters, and modifies them according to the passed
    arguments. You can add/modify parameters by passing in the desired value for
    those parameters, or even delete them by passing a blank string.

    Example:
    If the current URL is: http://example.com/?a=0&b=1
    http://example.com/{% modify_query_params b=4 %}
      --> http://example.com/?a=0&b=4
    http://example.com/{% modify_query_params b="" c=2 %}
      --> http://example.com/?a=0&c=2
    http://example.com/{% modify_query_params a="" b="" %}
      --> http://example.com/
    """
    request = context['request']
    params = request.GET.copy()
    for key, value in kwargs.items():
        if value == '':
            if key in params:
                del params[key]
        else:
            params[key] = value
    return ('?' + params.urlencode()) if params else ''


@register.assignment_tag
def get_api_key_params(user):
    """Assign to a context variable a query string for the given user's API key.

    Usage in templates:
    {% load template_utils %}
    {% get_api_key_params user as api_params %}
    {{ api_params }}

    would output the string:  'user=<user's pk>&key=<user's API key>'
    for the user object "user". This would often be used to append to a URL.
    """
    if user and user.is_authenticated():
        api_key, _ = APIKey.objects.get_or_create(user=user)
        return urlencode({'user': user.pk, 'key': api_key.key})
    return ''


@register.simple_tag(takes_context=True)
def full_url(context, view, *args, **kwargs):
    """Generate a full URL with protocol and domain given a view and optional
    (keyword) arguments.

    Usage in templates (same as Django's built-in url template tag):
    {% load template_utils %}
    {% full_url 'app:object_view' object.pk %}
    """
    if 'request' in context:
        is_secure = context['request'].is_secure()
    else:
        # Assume a secure connection if cannot be determined
        is_secure = True
    protocol = 'https' if is_secure else 'http'

    return '{protocol}://{domain}{relative_url}'.format(
        protocol=protocol,
        domain=settings.HOSTNAME,
        relative_url=reverse(view, args=args, kwargs=kwargs))
