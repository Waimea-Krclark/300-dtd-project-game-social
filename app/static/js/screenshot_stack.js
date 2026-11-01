document.addEventListener('DOMContentLoaded', function () {
    var mainEl = document.querySelector('#main-slider');
    var thumbEl = document.querySelector('#thumbnail-slider');
    var vertEl = document.querySelector('#vertical-slider');

    if (!mainEl || !thumbEl || !vertEl) return;
    var main = new Splide('#main-slider', {
        type: 'fade',
        rewind: true,
        pagination: false,
        arrows: true,        // prev/next arrows like your sketch
    });

    var thumbnails = new Splide('#thumbnail-slider', {
        fixedWidth: 100,
        fixedHeight: 60,
        gap: 10,
        rewind: true,
        pagination: false,
        isNavigation: true,  // makes thumbnails clickable
        arrows: false,
        cover: true,         // crops thumbnails to fill their box
        focus: 'center',
        breakpoints: {
            600: { fixedWidth: 60, fixedHeight: 44 },
        },
    });

    var vertical = new Splide( '#vertical-slider', {
        direction: 'ttb',
        height   : '30rem',
        perPage  : 2,  
        perMove  : 1,  
        isNavigation: true,
        arrows: false,
        gap: 0,
        drag   : 'free',
        snap   : true,
    } );



    main.sync(thumbnails);
    main.mount();
    thumbnails.mount();
    vertical.mount();
});