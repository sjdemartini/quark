$(function() {
  setupNav();
  setupDropdowns();
  setupForms();
});


/**
 * Setup for navigation bar actions (for narrow viewport functionality, such
 * as showing or hiding the nav elements).
 */
function setupNav() {
  var nav = $('#nav');
  var mediumWidth = 820;

  // wasNarrow refers to whether the window width (viewport) was narrow in the
  // previous call to the navResize function. Note that this is necessary as an
  // indicator for whether the window width just changed to become narrow (as
  // opposed to a window resive event in which the width remains narrow).
  var wasNarrow = $(window).width < mediumWidth;

  /**
   * Toggle the height of an element.
   *
   * selector - the identifier of the element for which we toggle the height
   * time - how long to take (default: 300ms)
   */
  var heightToggle = function(selector, time) {
    if (typeof(time) === 'undefined') {
      time = 300;
    }
    $(selector).stop(true, true).slideToggle(time);
  }

  // Controls toggle of main nav bar
  $('#nav-menubar').click(function(event) {
    heightToggle(nav);
  });

  // Manage submenus. Select and modify all subnested ul elements (indicating a
  // submenu beneath an element in the nav list):
  var navSubMenus = $('ul ul', nav);
  navSubMenus.each(function(index) {
    var subMenu = $(this);

    // Add buttons used for expanding sub-menus of parent navigation elements:
    var subMenuButton = $('<div class="nav-child-arrow-container">'
      + '<div class="nav-child-arrow"></div></div>');
    // Add to the parent of the submenu the submenu toggle button:
    subMenu.parent().prepend(subMenuButton);

    // Add fields to the actual HTML element for the subMenuButton:
    var subMenuButtonElem = subMenuButton.get(0);

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
  var navResize = function() {
    if ($(window).width() > mediumWidth) {
      // Wide viewport
      if (wasNarrow) {
        // First, hide all submenu elements, since they were taken out of the
        // flow in the narrow viewport
        navSubMenus.hide();

        // Make sure nav bar is shown, first hiding and then showing, to ensure
        // that the view is force-refreshed after submenu elements are hidden
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
      navSubMenus.each(function(index) {
        if (this.menuButton.closedSubMenu) {
          heightToggle(this, 0);
        }
      });
      wasNarrow = true;
    }
  };

  // Initialize the nav by calling navResize:
  navResize();

  // Set a window resize event to ensure that elements display correctly when
  // the browser window is resized
  $(window).resize(function() {
    navResize();
  });
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
  requiredFields.children('input').each(function() {
    this.required = true;
  });

  // If a form has required fields (and it isn't a "narrow" form, like is used
  // on the login screen), add a note above the form to explain that an
  // asterisk denotes a required field:
  requiredFields.parents('form').not('.form-narrow').before(
    '<div class="form-required-message">Required *</div>');
}

var formErrorClass = 'form-entry-error';
var formErrorMsgClass = 'error';

/**
 * Apply an error to a form fieldname.
 */
function apply_form_field_error(fieldname, error, shouldFocus) {
  var input = $('#id_' + fieldname);
  if (shouldFocus) {
    input.focus();
  }
  var container = input.parent();
  var error_msg = $('<span></span>').addClass(formErrorMsgClass).text(error[0]);
  container.addClass(formErrorClass);
  error_msg.insertAfter(input);
}

/**
 * Apply a general message above an element on the current page.
 *
 * @param message is the error message that should be displayed.
 * @param form is the form, above which the error message will be added.
 */
function add_error_message(message, form) {
  var msg = $('<div></div>').addClass('message error').text(message);
  $(form).before(msg);
}


/**
 * Clear error markup on form fields. Useful for when a form is resubmitted.
 */
function clear_form_field_errors(form) {
  var fieldsWithErrors = $('.' + formErrorClass, $(form));
  // Remove the error class from the form fields with errors
  fieldsWithErrors.removeClass(formErrorClass);
  // Remove the error messages from those fields
  $('.' + formErrorMsgClass, fieldsWithErrors).remove();
}
