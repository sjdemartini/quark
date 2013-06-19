from django import template
from django.views.debug import get_safe_settings


register = template.Library()
safe_settings = get_safe_settings()


@register.simple_tag
@register.assignment_tag(name='settings_assign')
def settings(name):
    """Returns the current value of a Django settings attribute.

    The method returns the settings value corresponding to the given attribute
    name, or returns an empty string if the name is not defined.

    Usage in templates:
    {% load settings_values %}
    {% settings 'IT_ADDRESS' %}

    would output the value of the attribute settings.IT_ADDRESS. Similarly,

    {% settings_assign 'IT_ADDRESS' as it_addr %}

    would save the value of the attribute settings.IT_ADDRESS into a context
    variable it_addr.
    """
    return safe_settings.get(name, '')
