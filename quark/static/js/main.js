$(function() {
  // Call the setup functions defined below:
  setupNav();
  setupDropdowns();
  setupForms();


  /**
   * Setup for navigation bar actions (for narrow viewport functionality, such
   * as showing or hiding the nav elements).
   */
  function setupNav() {
    /**
     * Return true if the viewport is within the medium viewport.
     */
    function isNarrow() {
      // Detect whether the browser is "narrow" (not wide viewport) by seeing
      // if the nav menubar is visible. If so, then the viewport is narrow
      // (since the menubar is only shown for narrow viewports).
      // Note that this method ensure consistency with the CSS media-queries,
      // rather than calculating viewport width using JS, which may be
      // inconsistent.
      return $('#nav-menubar').is(':visible');
    }

    /**
     * Toggle the height of an element.
     *
     * selector - the identifier of the element for which we toggle the height
     * time - how long to take (default: 300ms)
     */
    function heightToggle(selector, time) {
      if (typeof(time) === 'undefined') {
        time = 300;
      }
      $(selector).stop(true, true).slideToggle(time);
    }

    var nav = $('#nav');  // The nav bar

    // wasNarrow refers to whether the window width (viewport) was narrow in
    // the previous call to the navResize function. Note that this is necessary
    // as an indicator for whether the window width just changed to become
    // narrow (as opposed to a window resive event in which the width remains
    // narrow). Initialize as false, since haven't called navResize before:
    var wasNarrow = false;

    // The "menubar" toggles visibility of the main navigation options when the
    // viewport is narrow
    $('#nav-menubar').click(function() {
      heightToggle(nav);
    });

    // Manage submenus. Select and modify all subnested ul elements (indicating
    // a submenu beneath an element in the nav list):
    var navSubMenus = $('ul ul', nav);
    navSubMenus.each(function() {
      var subMenu = $(this);

      // Add buttons used for expanding sub-menus of parent navigation elements:
      var subMenuButton = $('<div class="nav-child-arrow-container">' +
        '<div class="nav-child-arrow"></div></div>');
      // Add to the parent of the submenu the submenu toggle button:
      subMenu.parent().prepend(subMenuButton);

      // Get the actual HTML element for the subMenuButton:
      var subMenuButtonElem = subMenuButton.get(0);

      // Add fields for the HTML element:
      // "closedSubMenu" indicates whether the user collapsed the submenu. This
      // saves state if the user goes between wide and narrow viewports.
      // Initialize all submenus as collapsed.
      subMenuButtonElem.closedSubMenu = true;

      // "subMenu" is the actual submenu ul element, for which this button
      // controls the visibility
      subMenuButtonElem.subMenu = subMenu;

      // Similarly, add to this element a pointer to the subMenuButton:
      this.menuButton = subMenuButtonElem;

      subMenuButton.on('click', function(event) {
        event.preventDefault();
        heightToggle(this.subMenu);
        this.closedSubMenu = !this.closedSubMenu;
      });
    });

    // Function to ensure proper display when resizing of page occurs
    function navResize() {
      if (!isNarrow()) {
        // Wide viewport
        if (wasNarrow) {
          // First, hide all submenu elements, since they were taken out of the
          // flow in the narrow viewport
          navSubMenus.hide();

          // Make sure nav bar is shown, first hiding and then showing, to
          // ensure that the view is force-refreshed after submenu elements are
          // hidden
          nav.hide();
          heightToggle(nav, 0);

          // Now open all subnavs so that they can be drop downs
          heightToggle(navSubMenus, 0);
        }
        wasNarrow = false;
      } else if (!wasNarrow) {
        // Just became a narrow viewport (since window is now narrow but was not
        // before), so hide the nav bar:
        nav.hide();

        // Close all subnavs that were closed by the user:
        navSubMenus.each(function() {
          if (this.menuButton.closedSubMenu) {
            heightToggle(this, 0);
          }
        });
        wasNarrow = true;
      }
    }

    // Set a window resize event to ensure that elements display correctly when
    // the browser window is resized
    var resizeId;
    $(window).resize(function() {
      clearTimeout(resizeId);  // Stop any navResize call currently running
      resizeId = setTimeout(navResize, 0);
    });

    // Initialize the nav by calling navResize:
    navResize();
  }


  /**
   * Setup for login dropdown menu toggling.
   */
  function setupDropdowns() {
    // Ensure all dropdowns initially hidden on page ready
    $('.dropdown').hide();

    // Make clicks anywhere in HTML body close the login dropdowns
    $('html').click(function() {
      $('.dropdown').hide();
    });
    // Make clicks on dropdown-title toggle the appropriate dropdown and close
    // others
    $('.dropdown-title').click(function(event) {
      var thisDropdown = $(this).next();
      $('.dropdown').not(thisDropdown).hide();
      thisDropdown.toggle();
      // Prevent the click from propagating to the document body
      event.stopPropagation();
    });
  }


  /**
   * Setup additional form behavior for required inputs.
   */
  function setupForms() {
    var requiredFields = $('.form-entry-required');

    // Use the HTML5 "required" attribute on input elements:
    requiredFields.find('input, textarea').each(function() {
      this.required = true;
    });

    // If a form has required fields (and it isn't a "narrow" form, like is used
    // on the login screen), add a note above the form to explain that an
    // asterisk denotes a required field:
    requiredFields.parents('form').not('.form-narrow').before(
      '<div class="form-required-message">Required *</div>');
  }
});



// Below are variables and functions used for forms and form error-handling.
// showFormErrors and clearFormFieldErrors are global functions to be used
// elsewhere.
/* exported showFormErrors, clearFormFieldErrors */
var formErrorClass = 'form-entry-error';
var formErrorMsgClass = 'form-errors';


/**
 * Show the provided form errors on the page.
 *
 * Also focus on the first field that has an error (if any).
 *
 * The function is useful when form errors are returned in an AJAX request
 * and should be displayed.
 *
 * @param errors is an object, mapping field names to a list of errors for the
 * corresponding field name. The object can also include a key '__all__', which
 * is used to indicate that the error is applied to the entire form, rather
 * than a specific field.
 */
function showFormErrors(form, errors) {
  // Apply focus to the first field that has an error
  var isFocused = false;
  $.each(errors, function(key, value) {
    // Iterate over the errors list, which maps field names to errors
    if (key === '__all__') {
      addErrorMessage(value[0], form);
    } else {
      applyFormFieldErrors(key, value, !isFocused);
      isFocused = true;
    }
  });


  /**
   * Apply a list of errors (or a single error) to a form fieldname.
   */
  function applyFormFieldErrors(fieldname, errors, shouldFocus) {
    var input = $('#id_' + fieldname);
    if (shouldFocus) {
      input.focus();
    }
    var container = input.parents('.form-entry');
    container.addClass(formErrorClass);

    var errorContainer = $('<div></div>').addClass(formErrorMsgClass);
    var errorList = $('<ul class="errorlist"></ul>');
    // For convenience and consistency, make sure "errors" is an array, so that
    // a for-each loop can be used to add error messages
    if (! $.isArray(errors)) {
      errors = [errors];
    }
    $.each(errors, function(index, error) {
      errorList.append($('<li class="error"></li>').text(error));
    });
    errorContainer.append(errorList);
    errorContainer.insertAfter(input);
  }


  /**
   * Apply a general message inside a form element on the current page.
   *
   * @param message is the error message that should be displayed.
   * @param form is the form, above which the error message will be added.
   */
  function addErrorMessage(message, form) {
    var msg = $('<div></div>').addClass('message error').text(message);
    $(form).prepend(msg);
  }
}


/**
 * Clear error markup on a form. Useful for when a form is resubmitted.
 */
function clearFormFieldErrors(form) {
  var fieldsWithErrors = $('.' + formErrorClass, $(form));
  // Remove the error class from the form fields with errors
  fieldsWithErrors.removeClass(formErrorClass);
  // Remove the error messages from those fields
  $('.' + formErrorMsgClass, fieldsWithErrors).remove();
  // Remove general error messages applied to the form:
  $('.message.error', $(form)).remove();
}
