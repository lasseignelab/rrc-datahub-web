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

    // Fixes nested-interactive on dcc.Checklist (#group-select).
    //
    // Dash renders the checklist as role="listbox" with each option as
    // <label role="option" aria-selected="..."> wrapping <input type="checkbox">.
    // role="listbox" is an interactive ARIA role; the axe nested-interactive rule
    // rejects focusable descendants inside interactive roles — aria-hidden +
    // tabindex=-1 do not satisfy this check because the rule tests DOM structure.
    //
    // Fix: replace role="listbox" with role="group" (the correct ARIA grouping
    // role for a set of related checkboxes) and remove role="option"/aria-selected
    // from each label so the native <label>+<input> pattern takes over.
    // role="group" is not an interactive role, so nested checkboxes are allowed.
    function fixChecklistARIA() {
        var container = document.getElementById("group-select");
        if (!container) { return; }

        if (container.getAttribute("role") === "listbox") {
            container.setAttribute("role", "group");
        }

        container.querySelectorAll("[role=\"option\"]").forEach(function (opt) {
            opt.removeAttribute("role");
            opt.removeAttribute("aria-selected");
        });

        // Remove the aria-hidden/tabindex applied by the previous approach —
        // checkboxes inside role="group" are not nested-interactive violations.
        container.querySelectorAll("input[type=\"checkbox\"]").forEach(function (cb) {
            if (cb.getAttribute("aria-hidden")) { cb.removeAttribute("aria-hidden"); }
            if (cb.getAttribute("tabindex") === "-1") { cb.removeAttribute("tabindex"); }
        });
    }

    function applyAll() {
        applyLabels();
        fixChecklistARIA();
    }

    var observer = new MutationObserver(applyAll);
    observer.observe(document.documentElement, {
        childList: true,
        subtree: true,
    });

    applyAll();
}());
