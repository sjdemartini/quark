/**
 * If there is a date or time field found (with the classes specified below),
 * invoke the necessary JQuery plugins.
 *
 * The functions are not called unless the fields are found, since the plugins
 * may be conditionally loaded depending on whether they are needed.
 */
$(function(){
  var dateField = $('.vDateField');
  if (dateField.length > 0) {
    dateField.datepicker({dateFormat: 'yy-mm-dd'});
  }

  var timeField = $('.vTimeField');
  if (timeField.length > 0) {
    timeField.timepicker();
  }
});
