import re

from django import template
from django.template.defaulttags import url


register = template.Library()


@register.tag
def ancestor(parser, token):
    """Checks whether a given URL is the "ancestor" of the current request's
    path.

    In other words, this tag is used the see whether the current page (the
    current request's path) is a "child" of some other URL (in the URL
    structure). This ability is useful for discovering whether a navigation
    element is "selected" or not.

    Usage:
    {% load ancestor %}

    If the argument to the ancestor tag matches the start of the current page's
    URL, it outputs "selected":

    Using a string as the URL path:
    {% ancestor '/arbitrary/path/' %}

    Or using variables, filters, etc.:
    {% ancestor some_variable|somefilter %}

    Or url reverse resolution:
    {% ancestor 'core:model_detail' model.pk %}

    Adapted from https://github.com/marcuswhybrow/django-lineage
    """
    # If there is only one argument (2 including tag name), parse it as a
    # variable
    bits = token.split_contents()
    if len(bits) == 2:
        arg = parser.compile_filter(bits[1])
    else:
        arg = None

    # Also pass all arguments to the original url tag
    url_node = url(parser, token)

    return AncestorNode(url_node, arg=arg)


class AncestorNode(template.Node):
    def __init__(self, url_node, arg=None):
        self.url_node = url_node
        self.arg = arg

    def get_path(self, context):
        # If the singular argument was provided and starts with a forward
        # slash, use it as the path
        if self.arg is not None:
            arg_output = self.arg.resolve(context)
            if re.match('/', arg_output):
                return arg_output

        # Otherwise derive the path from the url tag approach
        return self.url_node.render(context)

    def render(self, context):
        # If the "request" is not in the context, then the path cannot be
        # determined, so just return an empty string
        if 'request' not in context:
            return ''

        # Get the path of the current page
        current_path = context['request'].path

        path = self.get_path(context)

        # If the provided path is found at the root of the current path
        # (i.e., the path provided to the tag is an ancestor of the current
        # page), then return "selected"
        if re.match(path, current_path):
            return 'selected'
        return ''
