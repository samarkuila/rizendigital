(function($) {
    'use strict';

    // Mean Menu JS
    jQuery('.mean-menu').meanmenu({ 
        meanScreenWidth: "991"
    });

    // Navbar Area
    $(window).on('scroll', function() {
        if ($(this).scrollTop() >150){  
            $('.navbar-area').addClass("sticky-nav");
        }
        else{
            $('.navbar-area').removeClass("sticky-nav");
        }
    });

    // FAQ Accordion JS (each accordion works independently; the clicked question stays put on screen)
    $('.accordion').find('.accordion-title').on('click', function(e){
        e.preventDefault();
        var $title = $(this);
        var $item = $title.closest('.accordion-item');
        var $accordion = $title.closest('.accordion');
        var $content = $item.find('.accordion-content').first();
        var isOpen = $title.hasClass('active');
        var startTop = $title[0].getBoundingClientRect().top;

        // Close the other panels of THIS accordion only
        $accordion.find('.accordion-title').not($title).removeClass('active').attr('aria-expanded', 'false');
        var $others = $accordion.find('.accordion-content').not($content).stop(true, true);

        // Panels ABOVE the clicked question would push it up the screen while collapsing, so
        // close those instantly and correct the scroll in the same frame (nothing visible moves).
        // Panels below it can animate freely.
        var $above = $others.filter(function () {
            return !!(this.compareDocumentPosition($content[0]) & Node.DOCUMENT_POSITION_FOLLOWING);
        });
        $above.hide();
        $others.not($above).slideUp('fast');
        var drift = $title[0].getBoundingClientRect().top - startTop;
        if (drift) { window.scrollBy({ top: drift, left: 0, behavior: 'instant' }); }

        // Toggle this panel
        $title.toggleClass('active', !isOpen).attr('aria-expanded', String(!isOpen));
        if (isOpen) {
            $content.stop(true, true).slideUp('fast');
        } else {
            $content.stop(true, true).slideDown('fast');
        }
    });

    // Brand Slider 
     $('.brand-slider').owlCarousel({
        loop: true,
        margin: 30,
        nav: false,
        dots: false,
        autoplay: true,
        autoplayHoverPause: true,
        responsive:{
            0:{
                items: 2
            },
            568:{
                items: 3
            },
            768:{
                items: 5
            },
            1000:{
                items: 5
            }
        }
    })

    // Portfolio Slider 
    $('.portfolio-slider').owlCarousel({
        loop: true,
        margin: 30,
        dots: false,
        autoplay: true,
        autoplayHoverPause: true,
        nav: true,
        navText: [
            "<i class='bx bx-left-arrow-alt'></i>",
            "<i class='bx bx-right-arrow-alt'></i>"
        ],
        responsive:{
            0:{
                items: 1
            },
            768:{
                items: 2
            },
            1000:{
                items: 3
            }
        }
    })

    // Testimonial Slider 
    $('.testimonial-item-slider').owlCarousel({
        loop: true,
        items: 1,
        dots: false,
        autoplay: true,
        autoplayHoverPause: true,
        nav: true,
        navText: [
            "<i class='bx bx-left-arrow-alt'></i>",
            "<i class='bx bx-right-arrow-alt'></i>"
        ],
    })

    // Service Slider 
    $('.service-slider').owlCarousel({
        center: true,
        loop: true,
        margin: 30,
        dots: false,
        autoplay: true,
        autoplayHoverPause: true,
        nav: true,
        navText: [
            "<i class='bx bx-left-arrow-alt'></i>",
            "<i class='bx bx-right-arrow-alt'></i>"
        ],
        responsive:{
            0:{
                items: 1
            },
            768:{
                items: 2
            },
            1000:{
                items: 3
            }
        }
    })

    // Tabs
    $('#tabs-item li a').on('click', function(e) {
        $('#tabs-item li, #prices-content .active').removeClass('active').removeClass('fadeInUp');
        $(this).parent().addClass('active');
        var activeTab = $(this).attr('href');
        $( activeTab).addClass('active fadeInUp');
        e.preventDefault();
    });	

    // Popup Video 
    $('.play-btn').magnificPopup({
        disableOn: 700,
        type: 'iframe',
        mainClass: 'mfp-fade',
        removalDelay: 160,
        preloader: false,
        fixedContentPos: false
    });

    // Client Slider 
    $('.client-slider').owlCarousel({
        center: true,
        loop: true,
        margin: 30,
        dots: false,
        autoplay: true,
        autoplayHoverPause: true,
        nav: true,
        navText: [
            "<i class='bx bx-left-arrow-alt'></i>",
            "<i class='bx bx-right-arrow-alt'></i>"
        ],
        responsive:{
            0:{
                items: 1
            },
            768:{
                items: 2
            },
            1000:{
                items: 3
            }
        }
    })

    // Search Botton
    $('.close-btn').on('click',function() {
        $('.search-overlay').fadeOut();
        $('.search-btn').show();
        $('.close-btn').removeClass('active');
    });
    $('.search-btn').on('click',function() {
        $(this).hide();
        $('.search-overlay').fadeIn();
        $('.close-btn').addClass('active');
    });

    // Subscribe form
    $(".newsletter-form").validator().on("submit", function (event) {
        if (event.isDefaultPrevented()) {
            // Handle The Invalid Form...
            formErrorSub();
            submitMSGSub(false, "Please enter your email correctly");
        } else {
            // Everything Looks Good!
            event.preventDefault();
        }
    });
    function callbackFunction (resp) {
        if (resp.result === "success") {
            formSuccessSub();
        }
        else {
            formErrorSub();
        }
    }
    function formSuccessSub(){
        $(".newsletter-form")[0].reset();
        submitMSGSub(true, "Thank you for subscribing!");
        setTimeout(function() {
            $("#validator-newsletter").addClass('hide');
        }, 4000)
    }
    function formErrorSub(){
        $(".newsletter-form").addClass("animated shake");
        setTimeout(function() {
            $(".newsletter-form").removeClass("animated shake");
        }, 1000)
    }
    function submitMSGSub(valid, msg){
        if(valid){
            var msgClasses = "validation-success";
        } else {
            var msgClasses = "validation-danger";
        }
        $("#validator-newsletter").removeClass().addClass(msgClasses).text(msg);
    }
        
    // AJAX MailChimp
    $(".newsletter-form").ajaxChimp({
        url: "https://hibootstrap.us20.list-manage.com/subscribe/post?u=60e1ffe2e8a68ce1204cd39a5&amp;id=42d6d188d9", // Your url MailChimp
        callback: callbackFunction
    });

    // Back To Top Js
    $('body').append('<div id="toTop" class="top-btn"><i class="bx bx-chevrons-up"></i></div>');
    $(window).on('scroll',function () {
        if ($(this).scrollTop() != 0) {
            $('#toTop').fadeIn();
        } else {
            $('#toTop').fadeOut();
        }
    }); 
    $('#toTop').on('click',function(){
        $("html, body").animate({ scrollTop: 0 }, 0);
        return false;
    });

    // WOW JS (animate.css v4 uses the animate__ prefix, so animateClass must match)
    new WOW({
        animateClass: 'animate__animated'
    }).init();

    // Preloader JS
    jQuery(window).on('load',function(){
        jQuery(".preloader").fadeOut(500);
    });

    // Switch Btn
    $('body').append("<div class='switch-box'><label id='switch' class='switch'><input type='checkbox' onchange='toggleTheme()' id='slider'><span class='slider round'></span></label></div>");


    // Accessibility: give icon-only controls accessible names (plugins render them without any)
    function a11yFixes() {
        $('.owl-nav .owl-prev').removeAttr('role').attr('aria-label', 'Previous slide');
        $('.owl-nav .owl-next').removeAttr('role').attr('aria-label', 'Next slide');
        $('.owl-dots .owl-dot').removeAttr('role').each(function (i) { $(this).attr('aria-label', 'Go to slide ' + (i + 1)); });
        $('.meanmenu-reveal').attr({ 'aria-label': 'Open or close navigation menu', 'role': 'button' });
        $('#slider').attr('aria-label', 'Toggle dark mode');
    }
    a11yFixes();
    $(window).on('load resize', a11yFixes);

})(jQuery);

// function to set a given theme/color-scheme
function setTheme(themeName) {
    localStorage.setItem('bonsa_theme', themeName);
    document.documentElement.className = themeName;
}

// function to toggle between light and dark theme
function toggleTheme() {
    if (localStorage.getItem('bonsa_theme') === 'theme-dark') {
        setTheme('theme-light');
    } else {
        setTheme('theme-dark');
    }
}

// Immediately invoked function to set the theme on initial load
(function () {
    if (localStorage.getItem('bonsa_theme') === 'theme-dark') {
        setTheme('theme-dark');
        document.getElementById('slider').checked = false;
    } else {
        setTheme('theme-light');
      document.getElementById('slider').checked = true;
    }
})();


