// Patch ARIA issues on Dash components whose rendered HTML violates WCAG but
// whose component APIs do not expose the required props.
// A MutationObserver is used so patches apply on initial load and after
// multi-page navigation (Dash updates the DOM dynamically).
(function () {
    "use strict";

    // Map element id -> id of the sibling label element that names it.
    // Fixes WCAG 4.1.2: role=listbox and role=radiogroup require accessible names.
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

    // Fixes WCAG nested-interactive: dcc.Checklist renders role="option" labels
    // that wrap <input type="checkbox">. The checkbox is a redundant focusable
    // descendant — the role="option" + aria-selected pair already conveys
    // selection state to AT. Hide the checkbox from AT and remove it from the
    // tab order so the listbox/option keyboard pattern is the sole AT interface.
    function fixNestedInteractives() {
        var checkboxes = document.querySelectorAll(
            "#group-select input[type=\"checkbox\"]"
        );
        checkboxes.forEach(function (cb) {
            if (!cb.getAttribute("aria-hidden")) {
                cb.setAttribute("aria-hidden", "true");
                cb.setAttribute("tabindex", "-1");
            }
        });
    }

    function applyAll() {
        applyLabels();
        fixNestedInteractives();
    }

    var observer = new MutationObserver(applyAll);
    observer.observe(document.documentElement, {
        childList: true,
        subtree: true,
    });

    applyAll();
}());
