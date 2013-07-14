from django import template


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
