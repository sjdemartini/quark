// slideshow(selector)
// Initiates a slideshow in the given spot
// selector - the identifier of the element that contains the slideshow
// options - dictionary of options
var slideshow = function(selector, options) {
  // isString(s)
  // Helper function to check if a string
  // s - thing to check
  // returns true or false
  var isString = function(s) {
    return jQuery.type( s ) === 'string';
  };
  // isNumber(s)
  // Helper function to check if a number
  // s - thing to check
  // returns true or false
  var isNumber = function(s) {
    return jQuery.type( s ) === 'number';
  };
  // isBoolean(s)
  // Helper function to check if a boolean
  // s - thing to check
  // returns true or false
  var isBoolean = function(s) {
    return jQuery.type( s ) === 'boolean';
  };
  // makePositiveInt(s)
  // Helper function to make a number a positive integer
  // s - thing to round and make positive
  // returns positive integer
  var makePositiveInt = function(s) {
    return Math.round( Math.abs( s ) );
  };
  // centerAndResize(img, w, h)
  // Helper function to center and resize a absolutely position thing in an area
  // img - jQuery selected thing
  // w - width of area
  // h - height of area
  var centerAndResize = function(img, w, h) {
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
  };


  // Validate selector argument
  if (!(isString(selector))) {
    console.error('slideshow.js: invalid argument selector: [' +
        selector + ']');
    return;
  }

  // Checks options
  if (!(jQuery.type( options ) === 'object'))
    options = {};
  // The slide container id (can be different than the first argument)
  if (!(isString(options.slideContainer)))
    options.slideContainer = '#slideshowSlides';
  // The id of the left button
  if (!(isString(options.leftButtonID)))
    options.leftButtonID = '#slideshowLeft';
  // The id of the right button
  if (!(isString(options.rightButtonID)))
    options.rightButtonID = '#slideshowRight';
  // The beginning of the id of each slide.  Is followed by the index.
  if (!(isString(options.slideID)))
    options.slideID = '#slide-';
  // The class of the slides
  if (!(isString(options.slideClass)))
    options.slideClass = '.slide';
  // The class of the info boxes or the container of whatever else is displayed
  // with the slide other than the image.
  if (!(isString(options.slideInfoClass)))
    options.slideInfoClass = '.slideInfo';
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
    options.dimensionsRatio = makePositiveInt(options.dimensionsRatio);
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
    // switchTo(index)
    // Helper function to switch between two slides
    // index - index of the slide to switch to
    var switchTo = function(index) {
      // Verify index within range
      if (index < 0)
        index = slidesCount - 1;
      else if (index >= slidesCount)
        index = 0;
      indexTo = index;

      // Make the Info class disappear
      slides[indexOn].find(options.slideInfoClass).fadeTo(options.fadeTime, 0);
      slides[index].find(options.slideInfoClass).fadeTo(0, 0);
      slides[index].find(options.slideInfoClass).fadeTo(options.fadeTime, 1);

      // Fade the slides
      slides[indexOn].fadeOut(options.fadeTime);
      slides[index].fadeIn(options.fadeTime, function() {
        // This gets executed after the fading is done.
        indexOn = index;
        indexTo = -1;
        if (!hover) {
          currentTimeout = setTimeout(function() {
              switchTo(indexOn + 1);
            }, options.waitTime);
          }
        });
    };

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

  // Ensure dimensions of slideshow and set image dimensions
  var setWidth = function() {
    var w = $(options.slideContainer).innerWidth();
    var h = w * options.dimensionsRatio;

    // Center and resize the slide images
    if (options.centerAndResize) {
      centerAndResize(slides[indexOn].find('img'), w, h);
      if (indexTo != -1 && indexTo != indexOn) {
        centerAndResize(slides[indexTo].find('img'), w, h);
      }
    }

    if (options.addInfoHeight) {
      var infoH = $(options.slideInfoClass).outerHeight(true);
      h += infoH;
    }
    $(options.slideContainer).css('height', String(h));
    setTimeout(setWidth, 15);
  };
  setWidth();
};