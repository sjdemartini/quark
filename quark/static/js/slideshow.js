/**
 * Initiate a slideshow using the given selector and options, at the location
 * of the selected element.
 *
 * @param selector is the identifier of the element that contains the slideshow
 *  elements
 * @param options is the dictionary of options
 */
var slideshow = function(selector, options) {
  /**
   * Return true if the given value is a string.
   * @param s is the value to check
   * @returns a boolean value for whether s is a string
   */
  function isString(s) {
    return jQuery.type(s) === 'string';
  }

  /**
   * Return true if the given value is a number.
   * @param s is the value to check
   * @returns a boolean value for whether s is a number
   */
  function isNumber(s) {
    return jQuery.type(s) === 'number';
  }

  /**
   * Return true if the given value is a boolean.
   * @param s is the value to check
   * @returns a boolean value for whether s is a boolean
   */
  function isBoolean(s) {
    return jQuery.type(s) === 'boolean';
  }

  /**
   * Make a number a positive integer.
   * @param s is the value to round and make positive
   * @returns a positive integer representation of s
   */
  function makePositiveInt(s) {
    return Math.round(Math.abs(s));
  }

  /**
   * Center and resize an absolutely-position element in an area.
   * @param img is the jQuery object that is to be centered and resized
   * @parma w is the width of the new area
   * @param h is the height of the new area
   */
  function centerAndResize(img, w, h) {
    img.css('width', '');
    img.css('height', '');
    var ih = img.height(), iw = img.width();
    if (h * iw / ih > w) { // Image is more wide
      img.width(w);
      // Snap to actual height because float math makes it a bit off
      var height = (Math.abs((w * ih / iw) - h) <= 1) ? h : (w * ih / iw);
      img.height(height);
      img.css('left', '0');
      img.css('top', Math.floor((h - (w * ih / iw)) / 2));
    } else { // Image is more tall
      // Snap to actual width because float math makes it a bit off
      var width = (Math.abs((h * iw / ih) - w) <= 1) ? w : (h * iw / ih);
      img.width(width);
      img.height(h);
      img.css('left',  Math.floor((w - (h * iw / ih)) / 2));
      img.css('top', '0');
    }
  }

  // Validate selector argument
  if (!(isString(selector))) {
    console.error('slideshow.js: invalid argument selector: [' +
        selector + ']');
    return;
  }

  // Checks options
  if (!(jQuery.type(options) === 'object'))
    options = {};
  // The slide container id (can be different than the first argument)
  if (!(isString(options.slideContainer)))
    options.slideContainer = '#slideshow-slides';
  // The id of the left button
  if (!(isString(options.leftButtonID)))
    options.leftButtonID = '#slideshow-left';
  // The id of the right button
  if (!(isString(options.rightButtonID)))
    options.rightButtonID = '#slideshow-right';
  // The beginning of the id of each slide.  Is followed by the index.
  if (!(isString(options.slideID)))
    options.slideID = '#slide-';
  // The class of the slides
  if (!(isString(options.slideClass)))
    options.slideClass = '.slide';
  // The class of the info boxes or the container of whatever else is displayed
  // with the slide other than the image.
  if (!(isString(options.slideInfoClass)))
    options.slideInfoClass = '.slide-info';
  // First slide index
  if (!(isNumber(options.firstSlideIndex)))
    options.firstSlideIndex = 0;
  else
    options.firstSlideIndex = makePositiveInt(options.firstSlideIndex);
  // The time between switching slides (ms)
  if (!(isNumber(options.waitTime)))
    options.waitTime = 3000;
  else
    options.waitTime = makePositiveInt(options.waitTime);
  // The time it takes to fade between slides (ms)
  if (!(isNumber(options.fadeTime)))
    options.fadeTime = 400;
  else
    options.fadeTime = makePositiveInt(options.fadeTime);
  // Whether to pause on hover.
  if (!(isBoolean(options.hoverPause)))
    options.hoverPause = true;
  // The ratio of height to width of the slideshow
  if (!(isNumber(options.dimensionsRatio)))
    options.dimensionsRatio = 2 / 3;
  else
    options.dimensionsRatio = Math.abs(options.dimensionsRatio);
  // Whether to add the info box height to the height of the slideshow
  if (!(isBoolean(options.addInfoHeight)))
    options.addInfoHeight = false;
  // Whether to remove the arrows if there is one slide
  if (!(isBoolean(options.removeArrowsIfOneSlide)))
    options.removeArrowsIfOneSlide = true;
  // Whether to center and resize the images
  if (!(isBoolean(options.centerAndResize)))
    options.centerAndResize = true;

  // The container for the slides
  var container = $(selector);
  if (container.length == 0) {
    console.error('slideshow.js: not able to find the container');
    return;
  }

  // Which slide is being showed
  var indexOn = options.firstSlideIndex;
  // Which slide is being transitioned to or -1 if not transitioning
  var indexTo = -1;
  // Whether the mouse is over the slideShow
  var hover = false;

  // Finds the number of slides
  var slidesCount = container.find(options.slideClass).length;
  if (slidesCount < 1) {
    console.error('slideshow.js: must be at least one slide');
    return;
  }

  // Ensures firstSlideIndex within boundaries
  options.firstSlideIndex = options.firstSlideIndex % slidesCount;

  // Finds the slides
  var slides = [];
  for (var i = 0; i < slidesCount; i++) {
    slides.push(container.find(options.slideID + i));
    if (i != options.firstSlideIndex) {
      slides[i].fadeOut(0);
    }
  }

  // Only animate if there is more than one slide
  if (slidesCount > 1) {
    /**
     * Switch to a new slide.
     * @parama index is the index of the slide to switch to
     */
    function switchTo(index) {
      // Verify index within range
      if (index < 0) {
        index = slidesCount - 1;
      } else if (index >= slidesCount) {
        index = 0;
      }
      indexTo = index;
      updateDimensions();

      // Fade to transition the slides
      slides[indexOn].fadeOut(options.fadeTime);
      slides[indexTo].fadeIn(options.fadeTime, function() {
        // This gets executed after the fading is done.
        if (indexTo >= 0) {
          // As a protective measure, only reset indexOn if indexTo is a valid
          // value:
          indexOn = indexTo;
        }
        indexTo = -1;
        if (!hover) {
          currentTimeout = setTimeout(function() {
            switchTo(indexOn + 1);
          }, options.waitTime);
        }
      });
    }

    // Start the wait until the next switch
    var currentTimeout = setTimeout(function() {
      switchTo(indexOn + 1);
    }, options.waitTime);

    // Disable the timeout on hover
    if (options.hoverPause) {
      container.hover(function() {
        window.clearTimeout(currentTimeout);
        hover = true;
      }, function() {
        // Executes when the hover stops
        currentTimeout = setTimeout(function() {
            switchTo(indexOn + 1);
          }, options.waitTime);
        hover = false;
      });
    }

    // Bind left right buttons
    $(options.leftButtonID).bind('click.slideshowNav', function() {
      if (indexTo == -1) {
        window.clearTimeout(currentTimeout);
        switchTo(indexOn - 1);
      }
    });
    $(options.rightButtonID).bind('click.slideshowNav', function() {
      if (indexTo == -1) {
        window.clearTimeout(currentTimeout);
        switchTo(indexOn + 1);
      }
    });
  } else {
    // There is only one slide
    if (options.removeArrowsIfOneSlide) {
      $(options.leftButtonID).remove();
      $(options.rightButtonID).remove();
    }
  }


  var setDimensionsId;
  /**
   * Ensure dimensions of slideshow and its images are correct.
   */
  function updateDimensions() {
    // Update the width using the setDimensions function, but cancel any
    // existing calls to setDimensions, as it will be overwritten anyway
    function setDimensions() {
      var w = $(options.slideContainer).innerWidth();
      var h = w * options.dimensionsRatio;

      // Check if we are in the middle of transitioning between slides, useful
      // to know if the next image should also be centered and resized and what
      // height the container should be
      var isTransitioning = (indexTo != -1) && (indexTo != indexOn);

      // Center and resize the slide images
      if (options.centerAndResize) {
        centerAndResize(slides[indexOn].find('img'), w, h);
        if (isTransitioning) {
          centerAndResize(slides[indexTo].find('img'), w, h);
        }
      }

      if (options.addInfoHeight) {
        var slideIndex;
        if (isTransitioning) {
          slideIndex = indexTo;
        } else {
          slideIndex = indexOn;
        }
        var infoH = $(options.slideInfoClass).eq(slideIndex).outerHeight(true);
        h += infoH;
      }
      $(options.slideContainer).css('height', h);
    }

    // Stop any setDimensions call currently running and then call setDimensions
    clearTimeout(setDimensionsId);
    setDimensionsId = setTimeout(setDimensions, 0);
  }

  // Set a window resize event to ensure that the slideshow displays correctly
  // when the browser window is resized
  $(window).resize(function() {
    updateDimensions();
  });

  // Initialize the size by calling updateDimensions
  updateDimensions();
};
