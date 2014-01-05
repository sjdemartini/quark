import json

from django.http import HttpResponse
from django.views.generic import TemplateView


# Map of status codes to the default response messages:
JSON_RESPONSE_MESSAGES = {
    400: 'Invalid request.',
    403: 'Permission denied.',
    404: 'Not found.',
    405: 'HTTP method not allowed.',
    500: 'Internal server error.'
}

# Map of status codes to the default "status" messages included in responses:
JSON_RESPONSE_STATUSES = {
    400: 'fail',
    403: 'fail',
    404: 'fail',
    405: 'fail',
    500: 'error'
}


def json_response(data=None, status=200, message=None):
    """Returns an HttpResponse in JSON format, serializing the data parameter
    for the response and providing the status code given by the "status"
    parameter.

    If the response is a success (status 200), the serialized "data" parameter
    is used as the JSON response. No additional status or messages are included.

    The format of responses for failures or errors roughly follows the JSend
    specification (http://labs.omniti.com/labs/jsend). For failures/errors, a
    default message will be provided in the response depending on the status
    code (for instance, "Permission denied." for a 403), but the message can be
    overridden by providing the message parameter. The "data" parameter will be
    serialized and included in the JSON key "data" in the response.

    Supports status codes 200, 400, 403, 404, 405, and 500.

    The data defaults as None (JSON null), and the status defaults to 200
    (success).
    """
    if status == 200:
        json_data = data
    else:
        json_data = {}
        json_data['status'] = JSON_RESPONSE_STATUSES[status]
        # Set the message as the user's message, or as the default message if
        # the user did not provide one:
        json_data['message'] = message or JSON_RESPONSE_MESSAGES[status]
        json_data['data'] = data

    json_string = json.dumps(json_data)
    return HttpResponse(json_string, content_type='application/json',
                        status=status)


class JSONResponseMixin(object):
    """Mixin that can be used to render a JSON response.

    Views that use this mixin may need to override serialize_context to perform
    specific serialization for context data. Views can optionally set the
    "extra_data" field to a dictionary of additional serializable data for the
    response. See json_response above for more information on the format of
    JSON responses.

    Adapted from:
    docs.djangoproject.com/en/dev/topics/class-based-views/mixins/
    #more-than-just-html
    """
    extra_data = None

    def render_to_json_response(self, context=None, status=200,
                                **response_kwargs):
        """Return a JSON response, transforming 'context' to make the payload,
        adding in self.data, and using the "status" as the status code.
        """
        data = {}
        if self.extra_data:
            data.update(self.extra_data)
        if context:
            self.serialize_context(context)
            data.update(context)
        return json_response(data=data, status=status)

    def serialize_context(self, context):
        """Convert items in the context dictionary into serializable data.

        Subclassing views may need to do complex handling to ensure that
        arbitrary context objects -- such as Django model instances or
        querysets -- can be serialized as JSON (e.g., converting objects to
        dictionaries containing the objects' fields).
        """
        pass


class JSONView(JSONResponseMixin, TemplateView):
    """A standard view that returns a JSON response."""
    def render_to_response(self, context, **response_kwargs):
        return self.render_to_json_response(context, **response_kwargs)


class AjaxFormResponseMixin(JSONResponseMixin):
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
        super(AjaxFormResponseMixin, self).form_invalid(form)
        return self.render_to_json_response(form.errors, status=400)

    def form_valid(self, form):
        # We make sure to call the parent's form_valid() method because
        # it might do some processing. For instance, in the case of CreateView,
        # it will call form.save().
        super(AjaxFormResponseMixin, self).form_valid(form)
        return self.render_to_json_response()


class AjaxHybridFormResponseMixin(JSONResponseMixin):
    """Similar functionality to AjaxResponseMixin, but supports both HTML and
    JSON responses (depending on whether the request was an AJAX request).
    """
    def form_invalid(self, form):
        response = super(AjaxHybridFormResponseMixin, self).form_invalid(form)
        if self.request.is_ajax():
            return self.render_to_json_response(form.errors, status=400)
        else:
            return response

    def form_valid(self, form):
        # We make sure to call the parent's form_valid() method because
        # it might do some processing (in the case of CreateView, it will
        # call form.save() for example).
        response = super(AjaxHybridFormResponseMixin, self).form_valid(form)
        if self.request.is_ajax():
            return self.render_to_json_response()
        else:
            return response
