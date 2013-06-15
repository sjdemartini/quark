$(function() {
  /***** LOGIN DROPDOWN MENU TOGGLING *****/
  /* Make clicks anywhere in HTML body close the login dropdowns */
  $('html').click(function() {
    $('.dropdown').hide();
  });
  $('.dropdown').hide();
  $('.dropdown-title').click(function(event){
    var nextDropdown = $(this).next();
    $('.dropdown').not(nextDropdown).hide();
    nextDropdown.toggle();
    /* Prevent the click from propagating to the document body */
    event.stopPropagation();
  });
  /***** END LOGIN DROPDOWN MENU TOGGLING *****/

  /***** NAV MENU *****/
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
  $('#nav-menubar').click(function(event){
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
    if (!$('#nav-menubar').is(':visible')){
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
  /***** END NAV MENU *****/
});