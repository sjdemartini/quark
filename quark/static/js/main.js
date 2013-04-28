$(function() {
  /***** LOGIN DROPDOWN MENU TOGGLING *****/
  /* Make clicks anywhere in HTML body close the login dropdowns */
  $('html').click(function() {
    $('#login ul.dropdown').hide();
  });
  $('#login ul.dropdown').hide();
  $('#login .dropdown-title').click(function(event){
    var nextDropdown = $(this).next();
    $('#login ul.dropdown').not(nextDropdown).hide();
    nextDropdown.toggle();
    /* Prevent the click from propogating to the document body */
    event.stopPropagation();
  });
  /***** END LOGIN DROPDOWN MENU TOGGLING *****/
});
