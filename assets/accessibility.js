// Patch ARIA issues on Dash components whose rendered HTML violates WCAG but
// whose component APIs do not expose the required props.
// A MutationObserver is used so patches apply on initial load and after
// multi-page navigation (Dash updates the DOM dynamically).
(function () {
    "use strict";

    // Map element id -> id of the sibling label element that names it.
    // Fixes WCAG 4.1.2: role=listbox and role=radiogroup require accessible names.
    var LABEL_MAP = {
        "age-unit": "age-unit-label",
        "group-select": "group-select-label",
        "plot-age-select": "plot-age-label",
        "plot-sample-type-select": "plot-sample-type-label",
        "plot-sex-select": "plot-sex-label",
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
    var OPTION_CONTAINERS = [
        "group-select",
        "include-unknown-age",
        "plot-age-select",
        "plot-sample-type-select",
        "plot-sex-select",
        "stat-test",
    ];

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

    // dcc.Dropdown renders its "Clear selection" button as <a class="dash-dropdown-clear">
    // containing only an SVG icon — no text content. HTML_CodeSniffer flags this as a
    // link with no accessible content, even though aria-label is present. Adding a
    // visually-hidden span with the label text satisfies the rule without changing visuals.
    function fixDropdownClearButtons() {
        document.querySelectorAll("a.dash-dropdown-clear").forEach(function (a) {
            if (!a.querySelector(".visually-hidden")) {
                var span = document.createElement("span");
                span.className = "visually-hidden";
                span.textContent = "Clear selection";
                a.appendChild(span);
            }
        });
    }

    function applyAll() {
        applyLabels();
        fixOptionContainerARIA();
        fixDropdownClearButtons();
    }

    var observer = new MutationObserver(applyAll);
    observer.observe(document.documentElement, {
        childList: true,
        subtree: true,
    });

    applyAll();

    // Dataset row selection: apply highlight and aria-pressed immediately on
    // click for instant visual feedback while the Dash callback propagates.
    document.addEventListener("click", function (evt) {
        var btn = evt.target && evt.target.closest
            ? evt.target.closest("[data-bp]")
            : null;
        if (!btn) { return; }
        var table = document.getElementById("dataset-table");
        if (!table) { return; }
        table.querySelectorAll("[data-bp]").forEach(function (b) {
            b.setAttribute("aria-pressed", "false");
            var row = b.closest("tr");
            if (row) { row.classList.remove("dataset-row-selected"); }
        });
        btn.setAttribute("aria-pressed", "true");
        var selectedRow = btn.closest("tr");
        if (selectedRow) { selectedRow.classList.add("dataset-row-selected"); }
        // Notify Dash so downstream callbacks (plot, table, groups) update.
        if (window.dash_clientside && window.dash_clientside.set_props) {
            window.dash_clientside.set_props(
                "dataset-selected", { data: btn.getAttribute("data-bp") }
            );
        }
    });

    // Download handlers wired via event delegation rather than Dash clientside
    // callbacks. The buttons being Dash callback Inputs causes Dash 4 to apply a
    // loading-state lifecycle (unmount/remount) on every click, making them
    // visually flicker. Using plain DOM listeners bypasses that mechanism entirely.
    document.addEventListener("click", function (evt) {
        if (!evt.target || evt.target.id !== "download-png-btn") { return; }
        if (typeof window.Plotly === "undefined") { return; }
        var wrapper = document.getElementById("violin-plot");
        if (!wrapper) { return; }
        var plotEl = wrapper.querySelector(".js-plotly-plot") || wrapper;
        if (!plotEl._fullData || plotEl._fullData.length === 0) { return; }
        var metaEl = document.getElementById("download-meta");
        var metaPrefix = metaEl ? metaEl.textContent.trim().replace(/[^a-zA-Z0-9_-]/g, "_") : "";
        var filename = metaPrefix ? metaPrefix + "_tpm_expression" : "tpm_expression_plot";
        window.Plotly.toImage(plotEl, { format: "png", width: 1200, height: 700 })
            .then(function (dataUrl) {
                var a = document.createElement("a");
                a.download = filename + ".png";
                a.href = dataUrl;
                a.click();
            });
    });

    document.addEventListener("click", function (evt) {
        if (!evt.target || evt.target.id !== "download-csv-btn") { return; }
        var table = document.getElementById("tpm-data-table");
        if (!table) { return; }
        var headerCells = table.querySelectorAll("thead th");
        if (!headerCells.length) { return; }
        var rows = [];
        var headers = [];
        headerCells.forEach(function (th) {
            headers.push('"' + th.textContent.trim().replace(/"/g, '""') + '"');
        });
        rows.push(headers.join(","));
        table.querySelectorAll("tbody tr").forEach(function (tr) {
            var cells = [];
            tr.querySelectorAll("td").forEach(function (td) {
                cells.push('"' + td.textContent.trim().replace(/"/g, '""') + '"');
            });
            rows.push(cells.join(","));
        });
        var metaEl = document.getElementById("download-meta");
        var metaPrefix = metaEl ? metaEl.textContent.trim().replace(/[^a-zA-Z0-9_-]/g, "_") : "";
        var filename = metaPrefix ? metaPrefix + "_tpm_expression" : "tpm_expression_data";
        var blob = new Blob([rows.join("\n")], { type: "text/csv;charset=utf-8;" });
        var url = URL.createObjectURL(blob);
        var a = document.createElement("a");
        a.download = filename + ".csv";
        a.href = url;
        a.click();
        URL.revokeObjectURL(url);
    });
}());
