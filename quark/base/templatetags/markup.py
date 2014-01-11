import markdown as py_markdown

from django import template
from django.template.defaultfilters import stringfilter
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe


register = template.Library()


@register.filter(is_safe=True)
@stringfilter
def markdown(value):
    """Mimics the Django <=1.4 "markdown" template tag.

    Uses python markdown (http://pythonhosted.org/Markdown/index.html) to
    support markdown syntax
    (http://daringfireball.net/projects/markdown/syntax).

    Usage:
    {% load markup %}
    {{ markdown_content_var|markdown }}
    """
    return mark_safe(py_markdown.markdown(
        force_unicode(value),
        safe_mode='remove',
        enable_attributes=False))
