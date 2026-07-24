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

    // Fixes nested-interactive on dcc.Checklist and dcc.RadioItems.
    //
    // Both components render their container as role="listbox" with each option
    // as <label role="option" aria-selected="..."> wrapping a focusable input.
    // role="listbox" is an interactive ARIA role; the axe nested-interactive
    // rule rejects focusable descendants inside interactive roles regardless of
    // aria-hidden or tabindex=-1 (the rule tests DOM structure, not ARIA tree).
    //
    // Fix: replace role="listbox" with role="group" (correct ARIA grouping role
    // for a set of related inputs) and remove role="option"/aria-selected from
    // labels, restoring the native <label>+<input> pattern which is fully
    // accessible and contains no nested-interactive violation.
    var OPTION_CONTAINERS = ["group-select", "stat-test"];

    function fixOptionContainerARIA() {
        OPTION_CONTAINERS.forEach(function (id) {
            var container = document.getElementById(id);
            if (!container) { return; }

            if (container.getAttribute("role") === "listbox") {
                container.setAttribute("role", "group");
            }

            container.querySelectorAll("[role=\"option\"]").forEach(function (opt) {
                opt.removeAttribute("role");
                opt.removeAttribute("aria-selected");
            });
        });
    }

    function applyAll() {
        applyLabels();
        fixOptionContainerARIA();
    }

    var observer = new MutationObserver(applyAll);
    observer.observe(document.documentElement, {
        childList: true,
        subtree: true,
    });

    applyAll();
}());
