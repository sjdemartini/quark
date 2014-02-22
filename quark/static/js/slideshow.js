/**
 * A slideshow jQuery plugin. Usage:
 *
 * Usage:
 * $('my-slideshow-selector).slideshow();
 *
 * or usage with options:
 *
 * $('my-slideshow-selector').slideshow({
 *   slideInfoClass: '.info'
 * });
 *
 */
(function($) {
  /**
   * Center and resize an absolutely-position element in an area.
   * @param {jQuery object} img - object that is to be centered and resized
   * @param {number} w - the width of the new area
   * @param {number} h - the height of the new area
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

  /**
   * Calling slideshow() on a jQuery object creates a slideshow at the given
   * location, using any user-provided options.
   *
   * @param {object} options - The slideshow options (see below for all options
   *   and their defaults)
   */
  $.fn.slideshow = function(options) {
    var self = this;

    // Default options:
    var defaults = {
      // The id of the left button, to switch to the previous slide
      leftButtonID: '#slideshow-left',
      // The id of the right button
      rightButtonID: '#slideshow-right',
      // The prefix of the id of each slide. Is followed by the slide index.
      slideID: '#slide-',
      // The class of the slides
      slideClass: '.slide',
      // The class of the info boxes or the container of whatever else is
      // displayed with the slide other than the image.
      slideInfoClass: '.slide-info',
      // First slide index
      firstSlideIndex: 0,
      // The time between switching slides (number of ms)
      waitTime: 3000,
      // The time it takes to fade between slides (number of ms)
      fadeTime: 400,
      // Whether to pause on hover.
      hoverPause: true,
      // The ratio of height to width of the slideshow
      dimensionsRatio: 2 / 3,
      // Whether to add the info box height to the height of the slideshow
      addInfoHeight: false,
      // Whether to remove the arrows if there is one slide
      removeArrowsIfOneSlide: true,
      // Whether to center and resize the images
      centerAndResize: true
    };

    // Get the options, based on the defaults and any user-provided options:
    options = $.extend({}, defaults, options);

    // Which slide is being showed
    var indexOn = options.firstSlideIndex;
    // Which slide is being transitioned to or -1 if not transitioning
    var indexTo = -1;
    // Whether the mouse is over the slideShow
    var hover = false;

    // Finds the number of slides
    var slidesCount = self.find(options.slideClass).length;
    if (slidesCount < 1) {
      // If there are no slides, throw an error, since a slideshow can't be
      // created
      throw 'Error: No slides found.';
    }

    // Ensures firstSlideIndex within boundaries
    options.firstSlideIndex = options.firstSlideIndex % slidesCount;

    // Finds the slides
    var slides = [];
    for (var i = 0; i < slidesCount; i++) {
      slides.push(self.find(options.slideID + i));
      if (i != options.firstSlideIndex) {
        slides[i].fadeOut(0);
      }
    }

    // Only animate if there is more than one slide
    if (slidesCount > 1) {
      // Start the wait until the next switch
      var currentTimeout = setTimeout(function() {
        switchTo(indexOn + 1);
      }, options.waitTime);

      // Disable the timeout on hover
      if (options.hoverPause) {
        self.hover(function() {
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

    /**
     * Switch to a new slide.
     * @param {number} index - The index of the slide to switch to
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

    var setDimensionsId;
    /**
     * Ensure dimensions of slideshow and its images are correct.
     */
    function updateDimensions() {
      // Update the width using the setDimensions function, but cancel any
      // existing calls to setDimensions, as it will be overwritten anyway
      var setDimensions = function() {
        var w = self.innerWidth();
        var h = w * options.dimensionsRatio;

        // Check if we are in the middle of transitioning between slides,
        // useful to know if the next image should also be centered and resized
        // and what height the container should be
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
          var infoH = $(options.slideInfoClass).eq(
            slideIndex).outerHeight(true);
          h += infoH;
        }
        self.css('height', h);
      };

      // Stop any setDimensions call currently running and then call
      // setDimensions
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

    return self;
  };
}(jQuery));
