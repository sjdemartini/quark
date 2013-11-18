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
  // navMenuBarWasVisible refers to whether #nav-menubar was
  //   visible in the last loop
  var navMenuBarWasVisible = false;
  // navOpen refers to whether #nav is open or shut
  var navOpen = true;

  // heightToggle(selector, time)
  // Helper Function for toggling the height of a bar
  // selector - the identifier of the element for which we toggle the height
  // time - how long to take (default: 300ms)
  var heightToggle = function(selector, time) {
    if (typeof(time)==='undefined')
      time = 300;
    $(selector).stop(true, true).animate({ height: 'toggle' }, time);
  }

  // Controls toggle of main nav bar
  $('#nav-menubar').click(function(event) {
    heightToggle('#nav');
    navOpen = !navOpen;
  });

  // Manage Submenus
  $('#nav ul ul').each(function( index ) {
    var newHTML = '<div class="nav-child-arrow-container"><div '
      + 'class="nav-child-arrow"></div></div>';
    $(this).parent().prepend(newHTML);
    newHTML = $(this).prev().prev();
    // closedSubMenu is whether the user closed the tab (saves during
    //   wide version)
    newHTML[0].closedSubMenu = true;
    // actuallyClosed is whether the tab is actually closed
    newHTML[0].actuallyClosed = false;
    newHTML.bind('click.subMenu', function(event) {
      event.preventDefault();
      heightToggle($(this).next().next());
      this.closedSubMenu = !this.closedSubMenu;
      this.actuallyClosed = !this.actuallyClosed;
    }); // End of click.subMenu
  });

  // Loop to detect window size changes
  var navLoop = function() {
    if (!$('#nav-menubar').is(':visible')) {
      // Wide window -> make sure nav bar is shown
      if (!navOpen) {
        heightToggle('#nav', 0);
        navOpen = !navOpen;
      }
      if (navMenuBarWasVisible) {
        // Just became a wide window
        // -> Open all subnavs so that they can be drop downs
        $('#nav ul ul').each(function( index ) {
          var head = $(this).prev().prev()[0];
          if (head.actuallyClosed) {
            heightToggle(this, 0);
            head.actuallyClosed = !head.actuallyClosed;
          }
        });
        // -> Make sure nav bar is correct by forcing it to
        // recalculate its positioning
        heightToggle('#nav', 0);
        navOpen = !navOpen;
      }
    } else if (!navMenuBarWasVisible) {
      // Just became a thin window -> hide nav bar
      if (navOpen) {
        heightToggle('#nav', 0);
        navOpen = !navOpen;
        // Close all subnavs that were closed
        $('#nav ul ul').each(function( index ) {
          var head = $(this).prev().prev()[0];
          if (head.closedSubMenu) {
            heightToggle(this, 0);
            head.actuallyClosed = !head.actuallyClosed;
          }
        });
      }
    }
    navMenuBarWasVisible = $('#nav-menubar').is(':visible');
    /* Loops this function at ~60fps */
    setTimeout(navLoop, 15);
  };
  navLoop();
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
