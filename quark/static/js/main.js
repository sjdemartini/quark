$(function() {
  // Initialize constants
  var WIDTH_SMALL = 0;
  var WIDTH_SMALL_MED = 1;
  var WIDTH_MEDIUM = 2;
  var WIDTH_WIDE = 3;

  // Call the setup functions defined below:
  setupNav();
  setupDropdowns();
  setupLoginBar();
  setupForms();

  /**
   * Returns the proper constant based on the current screen state by detecting
   * whether certain test divs are visible.
   *
   * Note that this function ensures consistency with the CSS media-queries,
   * rather than calculating viewport width using JS, which may be
   * inconsistent.
   */
  function getScreenWidth() {
    if (!$('#width-test-small').is(':visible')) {
      return WIDTH_SMALL;
    }
    if (!$('#width-test-small-med').is(':visible')) {
      return WIDTH_SMALL_MED;
    }
    if (!$('#width-test-medium').is(':visible')) {
      return WIDTH_MEDIUM;
    }
    return WIDTH_WIDE;
  }


  /**
   * Setup for navigation bar actions (for narrow viewport functionality, such
   * as showing or hiding the nav elements).
   */
  function setupNav() {
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

    var nav = $('nav');  // The nav bar

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
        '<div class="nav-child-arrow fa fa-caret-right"></div></div>');
      // Add the child arrow container before the submenu list:
      subMenu.before(subMenuButton);

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

      // Add an on-click handler for expanding/collapsing the submenu
      subMenuButton.on('click', function(event) {
        event.preventDefault();

        // Toggle the arrow direction
        var arrow = $(this).children('.nav-child-arrow');
        arrow.toggleClass('fa-caret-right');
        arrow.toggleClass('fa-caret-down');

        // Toggle expanding/collapsing the submenu
        heightToggle(this.subMenu);
        this.closedSubMenu = !this.closedSubMenu;
      });
    });

    // Function to ensure proper display when resizing of page occurs
    function navResize() {
      if (getScreenWidth() == WIDTH_WIDE) {
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
      // If the style attribute is block (not the computed style)
      if (thisDropdown[0].style.display == 'block') {
        thisDropdown.hide();
      } else {
        thisDropdown.show();
      }
      // Prevent the click from propagating to the document body
      event.stopPropagation();
    });
  }


  /**
   * Setup login bar behavior for small screens.
   */
  function setupLoginBar() {
    // Insert the login bars
    var loginNarrow = $('<div id="login-narrow"></div>');
    $('#login').after(loginNarrow);

    // Get the current login dropdowns and loop through them
    var loginMenus = $('#login>ul>li>ul');
    loginMenus.each(function() {
      var menu = $(this);
      var inside = menu.clone();
      var slide = $('<div>');
      slide.append(inside);

      // Remove the dropdown class from the duplicated menu and then hide it
      inside.removeClass('dropdown')
        .removeAttr('style');
      slide.hide();

      // Add to the new bar
      loginNarrow.append(slide);

      // Get the button that controls the dropdown and make it toggle
      menu.parent().find('.dropdown-title').click(function() {
        $('#login-narrow>div').not(slide).hide(300);
        slide.stop(true, true).toggle(300);
        // Prevent the click from propagating to the document body
        event.stopPropagation();
      });
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
