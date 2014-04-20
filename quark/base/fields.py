from django import forms


class VisualDateWidget(forms.DateInput):
    """Extend the DateInput widget but tie in the calendar JQueryUI.

    It is recommended that this widget be used for any DateFields in forms.
    """
    class Media(object):
        # pylint: disable=C0103
        js = ('js/visual_datetime.js',)

    def __init__(self, *args, **kwargs):
        """Set the HTML class for the date input (as vDateField).

        Note that the JavaScript tied to the widget uses JQuery selectors with
        this class name. The JS sets the date format to match that of Django.
        """
        super(VisualDateWidget, self).__init__(*args, **kwargs)
        self.attrs['class'] = 'vDateField'


class VisualSplitDateTimeWidget(forms.SplitDateTimeWidget):
    """Extend the SplitDateTimeWidget but tie in the appropriate JavaScript.

    To be used by the VisualSplitDateTimeField below.
    """
    class Media(object):
        # pylint: disable=C0103
        css = {'all': ('css/libs/jquery.timepicker.css',)}
        js = ('js/visual_datetime.js', 'js/libs/jquery.timepicker.min.js')

    def __init__(self, time_format='%I:%M%p', *args, **kwargs):
        """Set the HTML class for the date input (as vDateField) and for the
        time input (as vTimeField).

        Note that the JavaScript tied to the widget uses JQuery selectors with
        these classes.
        """
        super(VisualSplitDateTimeWidget, self).__init__(
            *args, time_format=time_format, **kwargs)

        # widgets[0] is the DateInput widget for the date
        self.widgets[0].attrs['class'] = 'vDateField'

        # widgets[1] is the TextInput widget for the time
        self.widgets[1].attrs['class'] = 'vTimeField'


class VisualSplitDateTimeField(forms.SplitDateTimeField):
    """Extend SplitDateTimeField to use JQuery date and time inputs."""
    widget = VisualSplitDateTimeWidget

    def __init__(self, *args, **kwargs):
        """Sets the appropriate input_time_formats for the visual widget.

        The call to the superclass constructor specifies the input time formats
        allowed (matching the timepicker format used, which is 12-hour am/pm).
        The JS sets the date format to match that of Django.
        """
        super(VisualSplitDateTimeField, self).__init__(
            input_time_formats=['%I:%M%p', '%I:%M %p'], *args, **kwargs)
