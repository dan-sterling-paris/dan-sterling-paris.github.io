document.addEventListener('DOMContentLoaded', () => {
    const navToggle = document.getElementById('nav-toggle');
    const mainNav = document.getElementById('main-nav');
    const body = document.body;

    if (navToggle && mainNav) {
        navToggle.addEventListener('click', () => {
            const isOpen = mainNav.classList.toggle('is-open');
            body.classList.toggle('nav-open', isOpen); // Add/remove class on body

            // Update ARIA attribute for accessibility
            navToggle.setAttribute('aria-expanded', isOpen);

            // Change icon based on state
            if (isOpen) {
                navToggle.innerHTML = '&times;'; // Close icon (X)
            } else {
                navToggle.innerHTML = '&#9776;'; // Hamburger icon
            }
        });
    }

    // Optional: Close nav if clicking outside of it
    document.addEventListener('click', (event) => {
        if (mainNav.classList.contains('is-open')) {
            // Check if the click was outside the nav and not on the toggle button
            const isClickInsideNav = mainNav.contains(event.target);
            const isClickOnToggle = navToggle.contains(event.target);

            if (!isClickInsideNav && !isClickOnToggle) {
                mainNav.classList.remove('is-open');
                body.classList.remove('nav-open');
                navToggle.setAttribute('aria-expanded', 'false');
                navToggle.innerHTML = '&#9776;'; // Hamburger icon
            }
        }
    });

    // Optional: Add shadow to header on scroll
    // window.addEventListener('scroll', () => {
    //     if (window.scrollY > 50) { // Add shadow after scrolling 50px
    //         body.classList.add('scrolled');
    //     } else {
    //         body.classList.remove('scrolled');
    //     }
    // });
});