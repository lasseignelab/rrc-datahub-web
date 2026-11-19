
document.addEventListener("click", function (event) {
    const menu = document.getElementById("mobile-menu");

    if (!menu || !menu.open) {
        return;
    }

    // Close the menu when a navigation link is clicked.
    if (event.target.closest("#mobile-menu .nav-link")) {
        menu.open = false;
    }
});
