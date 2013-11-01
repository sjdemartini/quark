from functools import wraps
import json

from django.http import HttpResponse
from django.shortcuts import _get_queryset


def get_object_or_none(klass, *args, **kwargs):
    """
    This shortcut is modified from django.shortcuts.get_object_or_404
    Uses get() to return an object, or returns None if the object does not
    exist.

    klass may be a Model, Manager, or QuerySet object. All other passed
    arguments and keyword arguments are used in the get() query.

    Note: Like with get(), an MultipleObjectsReturned will be raised if more
    than one object is found.
    """
    queryset = _get_queryset(klass)
    try:
        return queryset.get(*args, **kwargs)
    except queryset.model.DoesNotExist:
        return None


def disable_for_loaddata(signal_handler):
    """Decorator that turns off signal handlers when loading fixture data.

    Taken from the Django documentation:
    https://docs.djangoproject.com/en/dev/ref/django-admin/
    #loaddata-fixture-fixture
    """
    @wraps(signal_handler)
    def wrapper(*args, **kwargs):
        if kwargs['raw']:
            return
        signal_handler(*args, **kwargs)
    return wrapper


class JSONResponseMixin(object):
    """Mixin that can be used to render a JSON response.

    Views that use this mixin may need to override convert_context_to_json to
    specify specific serialization for context data. Views can optionally
    override get_extra_data to provide additonal data for the response.

    Taken from:
    docs.djangoproject.com/en/dev/topics/class-based-views/mixins/
    #more-than-just-html
    """
    def render_to_json_response(self, context={}, **response_kwargs):
        """Return a JSON response, transforming 'context' to make the payload.
        """
        extra_data = self.get_extra_data()
        context.update(extra_data)
        data = self.convert_context_to_json(context)
        response_kwargs['content_type'] = 'application/json'
        return HttpResponse(data, **response_kwargs)

    def convert_context_to_json(self, context):
        """Convert the context dictionary into a JSON object."""
        # Note: This is a naive appraoch. You may need to do much more complex
        # handling to ensure that arbitrary objects -- such as Django model
        # instances or querysets -- can be serialized as JSON.
        return json.dumps(context)

    def get_extra_data(self):
        """Get extra data that will be included in the response.

        This method should be overridden by subclassing views if the views
        need to add additional serializable data for the response.
        """
        return {}


class AjaxResponseMixin(JSONResponseMixin):
    """Class-based view mixin to add AJAX support to a form.

    Only supports JSON responses. (See AjaxHybridResponseMixin for supporting
    both JSON and HTML responses.)

    Must be used with an object-based FormView (e.g. CreateView).

    Adapted from
    docs.djangoproject.com/en/dev/topics/class-based-views/generic-editing/
    #ajax-example
    """
    # A template is not needed for views using this mixin since only JSON
    # responses are returned, so add a default empty string for the template
    # name (which is a required field for FormViews):
    template_name = ''

    def form_invalid(self, form):
        super(AjaxResponseMixin, self).form_invalid(form)
        return self.render_to_json_response(form.errors, status=400)

    def form_valid(self, form):
        # We make sure to call the parent's form_valid() method because
        # it might do some processing. For instance, in the case of CreateView,
        # it will call form.save().
        super(AjaxResponseMixin, self).form_valid(form)
        return self.render_to_json_response()


class AjaxHybridResponseMixin(JSONResponseMixin):
    """Similar functionality to AjaxResponseMixin, but supports both HTML and
    JSON responses (depending on whether the request was an AJAX request).
    """
    def form_invalid(self, form):
        response = super(AjaxHybridResponseMixin, self).form_invalid(form)
        if self.request.is_ajax():
            return self.render_to_json_response(form.errors, status=400)
        else:
            return response

    def form_valid(self, form):
        # We make sure to call the parent's form_valid() method because
        # it might do some processing (in the case of CreateView, it will
        # call form.save() for example).
        response = super(AjaxHybridResponseMixin, self).form_valid(form)
        if self.request.is_ajax():
            return self.render_to_json_response()
        else:
            return response
