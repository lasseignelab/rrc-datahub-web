// Patch ARIA accessible names on Dash components whose rendered HTML roles
// require aria-labelledby but whose component APIs don't expose that prop.
// A MutationObserver is used so this works on initial load and after
// multi-page navigation (Dash updates the DOM dynamically).
(function () {
    "use strict";

    // Map element id -> id of the sibling label element that names it.
    var LABEL_MAP = {
        "group-select": "group-select-label",
        "stat-test": "stat-test-label",
    };

    function applyLabels() {
        Object.keys(LABEL_MAP).forEach(function (id) {
            var el = document.getElementById(id);
            if (el && !el.getAttribute("aria-labelledby")) {
                el.setAttribute("aria-labelledby", LABEL_MAP[id]);
            }
        });
    }

    var observer = new MutationObserver(applyLabels);
    observer.observe(document.documentElement, {
        childList: true,
        subtree: true,
    });

    applyLabels();
}());
