from django import forms


class VisualSplitDateTimeWidget(forms.SplitDateTimeWidget):
    """Extend the SplitDateTimeWidget but tie in the appropriate JavaScript.

    To be used by the VisualSplitDateTimeField below.
    """
    class Media:
        css = {'all': ('css/jquery.timepicker.css',)}
        js = ('js/visual_datetime.js', 'js/jquery.timepicker.min.js',)


class VisualSplitDateTimeField(forms.SplitDateTimeField):
    """Extend SplitDateTimeField to use JQuery date and time inputs."""
    widget = VisualSplitDateTimeWidget

    def __init__(self, *args, **kwargs):
        """
        Set the HTML class for the date input (as vDateField) and for the
        time input (as vTimeField). Note that the JavaScript tied to the
        widget (see above) uses JQuery selectors with these classes.
        The call to the superclass constructor specifies the input time formats
        allowed (matching the timepicker format used, which is 12-hour am/pm).
        """
        super(VisualSplitDateTimeField, self).__init__(
            input_time_formats=['%I:%M%p', '%I:%M %p'], *args, **kwargs)

        # widget.widgets[0] is the DateInput widget for the date
        self.widget.widgets[0].attrs['class'] = 'vDateField'
        # widget.widgets[1] is the TextInput widget for the time
        self.widget.widgets[1].attrs['class'] = 'vTimeField'
