from django import template


register = template.Library()


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
