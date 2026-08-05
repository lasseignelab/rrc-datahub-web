# Claude Changelog

A log of changes made by Claude Code in this project, newest first.

---

## 2026-08-05

### Add dataset count below the Dataset label
- `pages/charts.py`: Added `html.Span(id="dataset-count")` inline with the Dataset label. Added `Output("dataset-count", "children")` to `filter_datasets`; returns `"N dataset(s)"` (pluralised) on each filter change, or `"0 datasets"` on the early-exit path.

### Tighten Age column header and collapse equal-bound ranges
- `pages/charts.py`: Renamed table header from `"Age Range (days)"` to `"Age (days)"`. In `_fmt`, when both bounds are present and equal, returns just the single value as a string instead of `"lo–lo"`.

### Show distinct age ranges in dataset table column
- `pages/charts.py`: Changed `_get_dataset_table()` to accumulate distinct `(lower, upper)` integer pairs per bioproject into `age_ranges` (a set of tuples) instead of tracking a single min/max span. Added nested helpers `_fmt(lo, hi)` and `_sort_key(pair)` to format each pair as `"lo–hi"`, `"lo+"`, or `"–hi"`, and to sort by lower bound then upper bound. The returned dict key is now `"age_ranges"` (list of formatted strings, `["Unknown"]` when empty). Updated `_build_table_rows` to join the list with `", "`.

### Add Age Range (days) column to dataset table
- `pages/charts.py`: Extended `_get_dataset_table()` to also select `func.lower(Sample.age_range)` and `func.upper(Sample.age_range)` for each sample. The aggregation loop now tracks `age_min` and `age_max` per bioproject (min of all lower bounds, max of all upper bounds). The returned dict includes `"age_range"` formatted as `"X–Y"` (en-dash), or `"Unknown"` when all samples have a null age. Added `html.Th("Age Range (days)")` to the table header and `html.Td(row["age_range"])` to `_build_table_rows`.

### Apply human-readable sample type labels in dataset table
- `pages/charts.py`: In `_build_table_rows`, the Sample Type column now passes each raw value through `_readable_sample_type()` before joining, matching the labels shown in the filter checklist.

### Style dataset table selector buttons as radio buttons
- `pages/charts.py`: Changed the Select button label from `"Select"` to `""` (empty); visual content is now provided entirely by CSS.
- `assets/style.css`: Added radio-button CSS for `#dataset-table td:first-child button` — circular border, `::before` filled dot when `aria-pressed="true"`, and a visible `:focus-visible` ring. The button is 18 × 18 px with a 50% border-radius so it appears as a circle.

### Replace dataset dropdown with scrollable selection table
- `pages/charts.py`: Added `_get_dataset_table()` which applies the same filter logic as `_get_datasets_by_filters()` then aggregates distinct `scientific_name`, `underlying_variant`, `sample_type`, and `sex` values per bioproject. Added `_build_table_rows()` to render `html.Tr` elements with a Select button, BioProject ID, and the four aggregated columns. Replaced `dcc.Dropdown(id="dataset-select")` with a fixed-height (280 px) scrollable `html.Div` containing `html.Table(id="dataset-table")` with a sticky header and `html.Tbody(id="dataset-table-body")` populated by callbacks. Added `dcc.Store(id="dataset-selected")` to hold the selected bioproject. Replaced the old `filter_datasets` callback (which output dropdown options/value) with one that outputs `dataset-table-body.children` and `dataset-selected.data`. Added a new `select_dataset` pattern-matching callback (using `ALL`) that fires when any row Select button is clicked and updates `dataset-selected.data` with `allow_duplicate=True`. Updated `update_selectors`, `update_plot`, and `update_table` callbacks to use `Input("dataset-selected", "data")` instead of `Input("dataset-select", "value")`. Added `ALL`, `ctx` and `PreventUpdate` imports.
- `assets/style.css`: Added `#dataset-table` styles (border-collapse, sticky `th`, even-row stripe, `.dataset-row-selected` highlight in `#cce5ff`, hover state).
- `assets/accessibility.js`: Added event delegation listener on `[data-bp]` buttons to immediately apply `aria-pressed="true"` and `dataset-row-selected` class to the clicked row, giving instant visual feedback before the Dash callback round-trip completes.

### Add sex filter between sample type and age range
- `pages/charts.py`: Added `_get_all_sexes()` to query all distinct non-null `sex` values. Pre-loads `_all_sexes`. Added `sex-select` `dcc.Checklist` to the layout between Sample type and Age range. Extended `_get_datasets_by_filters()` with a `sexes` parameter filtered via `Sample.sex.in_(sexes)`. Updated `filter_datasets` callback with the new `Input("sex-select", "value")`.
- `assets/accessibility.js`: Added `"sex-select": "sex-select-label"` to `LABEL_MAP` and `"sex-select"` to `OPTION_CONTAINERS`.

### Add checkbox to control whether unknown-age samples are included in dataset filter
- `pages/charts.py`: Added `dcc.Checklist(id="include-unknown-age")` with a single option "Include samples with unknown age", checked by default, placed below the age range slider. Extended `_get_datasets_by_filters()` with `include_unknown_age: bool`; when True the age condition is `age_range IS NULL OR overlaps`; when False it is `age_range IS NOT NULL AND overlaps`. Updated `filter_datasets` callback with the new input, passing `bool(include_unknown_age)` (converts empty list to False).
- `assets/accessibility.js`: Added `"include-unknown-age"` to `OPTION_CONTAINERS` to apply the same role=group fix as other checklists.

### Add age range (days) filter to dataset filters section
- `pages/charts.py`: Added `from sqlalchemy import and_, func, or_`. Added `_get_age_range_bounds()` which uses PostgreSQL `lower()`/`upper()` on the NUMRANGE column to find the global min/max age in days (falls back to 0–365 if no data). Pre-loads `_age_min` and `_age_max` at startup. Extended `_get_datasets_by_filters()` with an `age_range` parameter; the filter includes samples where `age_range` is null (unknown age always passes) OR the sample's age_range overlaps the selected range. Added `dcc.RangeSlider(id="age-range-slider")` to the layout after Sample type with tooltips always visible. Updated `filter_datasets` callback with the new `Input("age-range-slider", "value")`.
- `assets/accessibility.js`: Added `labelRangeSliderInputs()` which uses `MutationObserver` (via `applyAll`) to set `aria-label` on the slider's two bare `<input type="number">` elements, fixing the WCAG 4.1.2 violation that pa11y detected.

### Add underlying variant filter to dataset filters section
- `pages/charts.py`: Added `_get_all_underlying_variants()` to query all distinct non-null `underlying_variant` values from the sample table. Added `underlying-variant-select` `dcc.Checklist` to the layout between scientific name and sample type. Extended `_get_datasets_by_filters()` to accept a third `underlying_variants` parameter and filter the dataset query against it. Updated `filter_datasets` callback with the new `Input("underlying-variant-select", "value")`.
- `assets/accessibility.js`: Added `"underlying-variant-select": "underlying-variant-label"` to `LABEL_MAP` and `"underlying-variant-select"` to `OPTION_CONTAINERS`.

### Remove cascade from scientific name to sample type
- `pages/charts.py`: Removed `filter_sample_types_by_scientific_name` callback and the `_get_sample_types_by_scientific_names` query function. Sample type options are now fixed (all types always visible). Scientific name and sample type still both feed into `filter_datasets` to narrow the dataset dropdown.

---

## 2026-08-04

### Organize Charts page into "Dataset filters" and "Plot parameters" sections
- `pages/charts.py`: Wrapped the scientific name, sample type, and dataset controls in an `html.Section` with heading "Dataset filters" (`id="dataset-filters-heading"`, `aria-labelledby="dataset-filters-heading"`). Wrapped the gene, groups, statistical test, buttons, and output area in a second `html.Section` with heading "Plot parameters" (`id="plot-parameters-heading"`, `aria-labelledby="plot-parameters-heading"`). Sections use `aria-labelledby` pointing to their H2 headings so screen readers can identify each landmark.

### Add scientific name filter above sample type; both filters narrow the dataset dropdown
- `pages/charts.py`: Added `_get_all_scientific_names()` to query all distinct non-null `scientific_name` values from the sample table. Added `_get_sample_types_by_scientific_names(scientific_names)` to return only the sample types present in samples of the selected organisms. Replaced `_get_datasets_by_sample_types()` with `_get_datasets_by_filters(scientific_names, sample_types)` which requires samples to match both filters simultaneously. Layout: added `scientific-name-select` `dcc.Checklist` above the existing `sample-type-select`, with all names selected by default. Added callback 1 (`filter_sample_types_by_scientific_name`) wired `scientific-name-select.value → sample-type-select.options + value`; updated callback 2 (`filter_datasets`) to take both `scientific-name-select.value` and `sample-type-select.value` as inputs so datasets reflect both active filters.
- `assets/accessibility.js`: Added `"scientific-name-select": "scientific-name-label"` to `LABEL_MAP` and `"scientific-name-select"` to `OPTION_CONTAINERS`.

### Add sample type filter that narrows the dataset dropdown
- `pages/charts.py`: Added `_get_all_sample_types()` to query all distinct non-null `sample_type` values across the entire database. Added `_get_datasets_by_sample_types(sample_types)` to return only bioproject accessions that contain at least one sample matching the selected types. Added `_SAMPLE_TYPE_LABELS` dict and `_readable_sample_type()` to convert raw database values to human-readable labels (underscores/hyphens → spaces, title-cased; with an override dict for values like "iPSC" that must not be title-cased). Layout: added `sample-type-select` `dcc.Checklist` above the dataset dropdown, showing all available sample types from the database with all selected by default. Added callback 1 (`filter_datasets_by_sample_type`) that takes the checklist value as input and updates `dataset-select.options` and `dataset-select.value`, preserving the current dataset if it is still in the filtered list.
- `assets/accessibility.js`: Added `"sample-type-select": "sample-type-label"` to `LABEL_MAP` and `"sample-type-select"` to `OPTION_CONTAINERS` so the checklist gets the same ARIA role fix as the groups checklist.

---

## 2026-07-31

### Fix pa11y CI failure: move no-data message out of table caption
- `pages/charts.py`: axe-core's "layout-table-caption" rule fired in CI because when no DB is available, `update_table` returned `[html.Caption("No data...")]` — a table containing only a caption and no `<th>` elements, which axe classifies as a layout table (layout tables must not have captions). Fix: added `html.P(id="table-status")` as a sibling above the table in `table-container`. The callback now outputs both `table-status.children` (the message string) and `tpm-data-table.children` (the table rows). No-data states write the message to the paragraph and return `[]` for the table, leaving the table empty rather than caption-only. When data is present the message is cleared and the table gets its normal caption + thead + tbody.

### Remove subscript Unicode from table column header
- `pages/charts.py`: Changed `log₁₀(TPM + 1)` → `log10(TPM + 1)` in the table `<th>`. The subscript Unicode characters rendered inconsistently and also appeared verbatim in the CSV export.

### Reorder button bar: toggle button left, download button right
- `pages/charts.py`: Moved `toggle-view-btn` ("Show table / Show plot") to the left of the download buttons. Added `marginRight: "8px"` to the toggle button for spacing. Removed `marginRight` from download buttons (now the last elements in the row).

### Add "Download table as CSV" button, sync download buttons with view toggle
- `pages/charts.py`: Added `html.Button("Download table as CSV", id="download-csv-btn")` (initially hidden) alongside the existing PNG download button. Extended the view-toggle `clientside_callback` with two additional outputs — `download-png-btn.style` and `download-csv-btn.style` — so the correct download button is always visible for the active view: PNG download when the plot is shown, CSV download when the table is shown.
- `assets/accessibility.js`: Added event-delegation click handler for `download-csv-btn`. Reads headers and rows directly from the rendered `tpm-data-table` DOM, builds a properly-escaped CSV string (double-quotes all fields, escapes internal quotes), derives the filename from the table caption, and triggers a client-side blob download — no server round-trip required.

### Fix table toggle: replace DOM event delegation with clientside_callback
- `pages/charts.py`: Replaced the `toggle-view-btn` click handler in `accessibility.js` with a Dash `clientside_callback`. The previous handler used direct DOM manipulation (`el.style.display = "none"`), which React's reconciler overwrites whenever any sibling callback (e.g., `update_table`) fires and re-renders part of the component tree. The `clientside_callback` updates `plot-container.style` and `table-container.style` through React's component prop system, so the toggle state persists across server callback re-renders. Button text and `aria-expanded` are still set via DOM manipulation inside the callback function — safe because `toggle-view-btn` is not a callback output and React does not reconcile it. Added `clientside_callback` to the Dash import.
- `assets/accessibility.js`: Removed the `toggle-view-btn` click event listener (now handled by the clientside callback). Download handler is unchanged.

### Add accessible toggleable table view for TPM expression data
- `pages/charts.py`: Added a "Show table / Show plot" toggle button (`id="toggle-view-btn"`, `aria-expanded`) alongside the download button. Added `id="plot-container"` wrapper around the graph and `id="table-container"` div (initially hidden) containing `html.Table(id="tpm-data-table")`. Added `id="view-status"` polite ARIA live region for screen-reader announcements. Added callback 4 (`update_table`) which builds an accessible HTML table of per-sample raw TPM and log₁₀(TPM+1) values for the current gene/group selection; the table is always populated in the background so toggling the view requires no server round-trip. Added `import math` for the log10 calculation.
- `assets/accessibility.js`: Added click event listener for `toggle-view-btn` that switches `display` on the two containers, updates `aria-expanded`, updates the button label, and writes a polite status message to the live region.
- `assets/style.css`: Added `.visually-hidden` CSS class (clip + position: absolute) for the live region. Added table styles: border-collapse, padding, header background, zebra-stripe rows, and `:focus-within` outline for keyboard navigation.

## 2026-07-29

### Fix download button appearing/disappearing due to graph layout reflow
- `pages/charts.py`: `dcc.Graph` with `responsive=True` (which unsets `figure.layout.height`) collapses its container to near-zero height when `figure={}` during a callback update, then re-expands to ~450 px when the figure loads. The button was positioned below the graph, so it shifted by ~450 px on every figure update — going off-screen and back, which the user saw as appearing/disappearing on every other interaction (open dropdown = one interaction, select value = next). Fix: moved the button above the graph so it is always in the upper viewport regardless of graph height, and added `minHeight: 450px` to the graph container to prevent the collapse reflow.

### Fix download button flicker by moving handler out of Dash callback system
- `assets/accessibility.js`: Added a document-level click event listener (event delegation) that handles the PNG download directly. The button was flickering because being a Dash `Input` causes Dash 4 to apply a loading-state lifecycle (unmount/remount) on every click. Wiring the handler in plain JavaScript bypasses that mechanism entirely.
- `pages/charts.py`: Removed the `clientside_callback` and the `html.Div(id="download-trigger")` that were no longer needed. The button (`id="download-png-btn"`) is now a plain HTML element with no Dash callback wiring.

### Fix blank PNG export and initial button-disappear attempt
- `pages/charts.py`: Removed the server-side `toggle_download_button` callback (callback 4) that controlled `download-png-btn.disabled`. That callback fired on every figure update, including transient `{}` states during dataset/gene selection changes, causing Dash to remount the button and making it visually disappear. The button is now always enabled; the clientside callback already guards against empty figures.
- `pages/charts.py`: Fixed blank PNG download. `dcc.Graph` renders a wrapper `<div id="violin-plot">` containing the actual Plotly element `<div class="js-plotly-plot">`. `Plotly.toImage` requires the inner element (which carries `_fullData`), not the wrapper. Updated clientside callback to `querySelector(".js-plotly-plot")` and check `_fullData.length` for data presence. Removed `State("violin-plot", "figure")` from the clientside callback — figure presence is now determined from the DOM element directly, avoiding the server round-trip.

## 2026-07-24

### Add accessible PNG download button for violin plot
- `pages/charts.py`: Replaced the inaccessible Plotly mode bar download icon (hidden via `displayModeBar: False`) with an `html.Button("Download plot as PNG")`. The button is disabled until a figure is rendered (callback 4) and calls `Plotly.downloadImage` via a clientside callback (callback 5). The filename is derived from the figure title (the selected gene name).

### Fix chart layout at 400% zoom (WCAG 1.4.10 Reflow)
- `pages/charts.py`: Added `config={"responsive": True}` and `style={"width": "100%"}` to `dcc.Graph` so Plotly resizes the SVG when the container width changes at high zoom levels. Also set `displayModeBar: False` (the mode bar has no accessible label).
- `components/tpm_violin_plot_plotly.py`: Moved legend below the chart (`orientation="h"`, `y=-0.25`, `margin.b=160`). At narrow viewports the long genotype labels previously occupied most of the horizontal space, leaving almost no room for the plot area.

### Wrap navbar in html.Nav landmark (WCAG region)
- `components/navbar.py`: Changed `html.Div` to `html.Nav` with `aria-label="Site navigation"`. The navbar content was outside any landmark, failing the axe region check. With this and the `<main>` added previously, all page content is now contained within landmarks.

### Add main landmark and skip navigation link (WCAG 2.4.1)
- `app.py`: Wrapped `page_container` in `html.Main(id="main-content")` so the page has a `<main>` landmark. Added a visually-hidden skip-to-main-content `html.A` as the first focusable element so keyboard users can bypass the repeated navbar.
- `assets/style.css`: Added `.skip-nav` CSS — off-screen when unfocused (`position:absolute; left:-9999px`), visible when focused (`position:static`).

### Extend nested-interactive fix to dcc.RadioItems (#stat-test)
- `assets/accessibility.js`: `dcc.RadioItems` uses the same `role="listbox"` / `role="option"` rendering pattern as `dcc.Checklist`. Renamed and generalized `fixChecklistARIA()` to `fixOptionContainerARIA()`, which now iterates both `#group-select` and `#stat-test` and applies the same `role="group"` substitution and `role="option"` removal.

### Fix nested-interactive: replace role=listbox with role=group on checklist (WCAG 4.1.2)
- `assets/accessibility.js`: Previous fix (`aria-hidden` + `tabindex=-1` on checkboxes) did not satisfy the axe nested-interactive rule, which tests DOM structure — any focusable element inside an interactive ARIA role fails regardless of those attributes. `fixChecklistARIA()` now replaces `role="listbox"` on `#group-select` with `role="group"` (correct grouping role for a set of related checkboxes) and removes `role="option"` / `aria-selected` from each label, restoring the native `<label>`+`<input>` pattern. `role="group"` is not an interactive role, so nested checkboxes are permitted.

### Fix nested-interactive violation in dcc.Checklist (WCAG 4.1.2)
- `assets/accessibility.js`: Added `fixNestedInteractives()`. Dash 4 renders `dcc.Checklist` as `role="listbox"` with each option as `<label role="option">` wrapping `<input type="checkbox">`. The checkbox is a focusable descendant inside an interactive ARIA role, violating WCAG nested-interactive. The fix sets `aria-hidden="true"` and `tabindex="-1"` on each checkbox so the `role="option"` + `aria-selected` pair is the sole AT interface — the correct ARIA listbox pattern.

### Fix missing ARIA accessible names on group-select and stat-test (WCAG 4.1.2)
- `assets/accessibility.js`: Created. A `MutationObserver` watches the DOM and patches `aria-labelledby` onto `#group-select` (role=listbox) and `#stat-test` (role=radiogroup) after Dash renders them. Dash 4's `dcc.Checklist` and `dcc.RadioItems` do not expose ARIA props in their component API, so the attribute must be applied via JavaScript. The observer handles both initial page load and multi-page navigation.
- `pages/charts.py`: Added `id="group-select-label"` to the "Groups" label and `id="stat-test-label"` to the "Statistical test" label so the observer has valid targets to reference.
- `.pa11yci`: Added `http://localhost:8050/charts` to the URL list so CI catches accessibility violations on the charts page.

## 2026-07-17

### Pin Python version to 3.13
- `.python-version`: Created with `3.13` so pyenv, uv, and other local tooling pin to Python 3.13 automatically.
- `.github/workflows/tests.yml`, `.github/workflows/accessibility.yml`: Changed `python-version: "3.13"` to `python-version-file: .python-version` so CI reads from the single source of truth.

## 2026-07-15

### Fix pyright reportOptionalMemberAccess on get_engine()
- `db/connection.py`: Pyright couldn't narrow the type of the global `_engine` after `_get_factory()` set it, so `get_engine()` appeared to return `Engine | None`. Switched to a local variable pattern with an explicit `-> Engine` return annotation so pyright can confirm the return is always non-None.

### Add get_engine() and fix etl/load.py import after lazy refactor
- `db/connection.py`: Added `get_engine()` public function that returns the lazily-created engine. The lazy refactor had removed the module-level `engine` name, breaking any caller that needed the raw engine (mypy, pylint, and pyright all caught this).
- `etl/load.py`: Updated import from `engine` to `get_engine` and changed the `engine.raw_connection()` call to `get_engine().raw_connection()`.

### Make DB engine lazy to fix CI import crash
- `db/connection.py`: Engine and session factory were built at module level, causing `KeyError: 'DB_HOST'` whenever the module was imported without database env vars present (CI, fresh checkouts). Deferred creation to the first `SessionLocal()` call so the module imports cleanly in all environments. Tests relying on the Dash app import now pass without a live database.

### Fix percy version conflict breaking CI
- `requirements.txt`: Updated `percy==1.1.1` to `percy==2.0.2` — `dash[testing]==4.1.0` declares a `percy>=2.0.2` dependency, so the old pin made the combined install impossible.
- `requirements-dev.txt`: Removed the redundant explicit `percy==1.1.1` pin; `dash[testing]` already pulls the correct version via its own dependency declaration.

### Pin dash[testing] version in requirements-dev.txt
- `requirements-dev.txt`: Pinned `dash[testing]==4.1.0` to match `dash==4.1.0` in `requirements.txt`. Without a version pin, CI was upgrading dash to 4.4.0 when installing dev dependencies, pulling in new transitive requirements (`janus`, `pydantic`, `percy-python-selenium`) not present in `requirements.txt` and breaking the test environment.

### Server-side gene search in charts dropdown
- `pages/charts.py`: Replaced full 78k-gene dropdown with server-side search. New `_search_genes(search)` queries the `gene` table directly (no sample_gene join) with an ILIKE prefix filter and a limit of 50 results. The gene dropdown now fires a callback on each keystroke and returns only matching genes, eliminating browser lag from rendering thousands of options. Split the previous single selector callback into two: one for gene options (search-driven) and one for group reset (dataset-driven).

---

### Connect charts page to PostgreSQL; remove file-based data loading
- `pages/charts.py`: Rewrote to query the database instead of reading CSV/TSV files. Dataset list, gene list, genotype list, and per-gene TPM values all come from the `dataset`, `sample`, `gene`, and `sample_gene` tables via SQLAlchemy ORM queries. Module-level startup queries are wrapped with logged fallbacks so the page degrades gracefully if the database is unavailable.
- `config.py`: Deleted. Dataset discovery was the only consumer; that logic now lives inline in `pages/charts.py` as a DB query.
- `components/data_utils.py`: Deleted. `melt_nfcore_tpm()` is no longer needed; the database returns data already in long format.
- `db/PRJNA285844/`: Deleted. The CSV/TSV staging files (`salmon.merged.gene_tpm.tsv`, `samplesheet.csv`, `extended_metadata.csv`) are replaced by the PostgreSQL database.

---

## 2026-07-14

### Move Testing before Running the app in Getting Started and section order
- `CLAUDE.md`: Swapped steps 5 and 6 in Getting Started so the test suite runs before starting the app. Moved the Testing section before Running the app in the document body and Table of Contents to match.

### Update CLAUDE.md: streamline Getting Started, expand ETL and Dependencies sections
- `CLAUDE.md`: Condensed Getting Started to step titles with links only (detail moved to the referenced sections). Expanded Dependencies section to include the full venv creation and install commands. Expanded Environment setup to clarify variables are filled in progressively across setup steps. Added GitHub Token instructions (fine-grained PAT creation and org admin approval steps) to the ETL load script section.

### Reorder CLAUDE.md sections to match Getting Started sequence
- `CLAUDE.md`: Reordered sections so the detailed reference sections appear in the same order as the Getting Started steps: Dependencies → Environment setup → Database → ETL load script → Running the app → Testing. Contributor sections (Linting, Code style, Accessibility, Git conventions, Pull requests) remain grouped at the end. Updated Table of Contents to match.

---

## 2026-07-10

### Document query function placement convention in CLAUDE.md
- `CLAUDE.md`: Added "Query functions" subsection under Database explaining when to use `db/queries.py` vs. writing queries inline in page/component files. Rule: shared queries (used in 2+ places) go in `db/queries.py`; single-use queries stay in the page or component that needs them.

---

### Centralize linter import suppression in config files; add pa11y to pre-commit gate
A MegaLinter image update introduced pylint `E0401` (import-error) and pyright `reportMissingImports` failures across all files that import third-party packages not installed in the Docker image. Rather than scattering inline `# pylint: disable=import-error` and `# type: ignore[import-untyped]` comments across 14 source files, suppression was moved to central config:
- `.mega-linter.yml`: Added `PYTHON_PYLINT_ARGUMENTS: "--disable=import-error"` and `PYTHON_MYPY_ARGUMENTS: "--disable-error-code=import-untyped"`.
- `pyproject.toml`: Added `[tool.pyright]` section with `reportMissingImports = "none"` and `reportMissingModuleSource = "none"`.
- Removed all `# pylint: disable=import-error` and `# type: ignore[import-untyped]` from every source file (`app.py`, `components/`, `pages/`, `db/`, `etl/`, `migrations/`, `tests/`).
- `CLAUDE.md`: Updated "Instructions for Claude Code" to require `npm run a11y` (with the app running) alongside `pytest --headless` and MegaLinter before every commit and push.

### Expand Database section in CLAUDE.md with PostgreSQL install instructions
- `CLAUDE.md`: Added "Installing PostgreSQL" subsection covering macOS (Homebrew), Windows (official installer), and Linux (apt-get). Added "Creating the database and user" subsection with `psql` commands. Added "Connecting the app" subsection showing how to populate `.env` and run `alembic upgrade head`.
- `.env.example`: Updated `DB_USER` to `rrc_user` and `DB_PASSWORD` to `yourpassword` to match the credentials shown in the CLAUDE.md Database section.

---

## 2026-07-09

### Add gene model, sample_gene mapping table, and TPM load functions
- `db/models.py`: Added `Gene` (Ensembl gene_id + gene_name) and `SampleGene` (composite PK on sample_id + gene_id, secondary index on gene_id for gene-centric queries) ORM models. Named `SampleGene` rather than `SampleGeneTpm` so additional expression metrics can be added as columns in the future.
- `migrations/versions/a1b2c3d4e5f6_create_gene_table.py`: Alembic migration to create the `gene` table.
- `migrations/versions/b2c3d4e5f6a7_create_sample_gene_table.py`: Alembic migration to create the `sample_gene` table with FKs to `sample` and `gene`.
- `etl/load.py`: Added `load_genes()` — reads gene_id and gene_name from the first TPM reference file (all 14 files share the same 78,317-row Ensembl annotation) and bulk-inserts new genes. Added `load_tpm()` — for each `staging/tpm/PRJNA*/salmon.merged.gene_tpm.tsv`, maps SRR column headers to sample IDs, then bulk-inserts (sample_id, gene_id, tpm) rows via psycopg2 `execute_values` in 10,000-row batches for performance. Samples already present in `sample_gene` are skipped (idempotent). Both functions are called from `__main__`.

### Fixed urllib3 version conflict in requirements.txt
- `requirements.txt`: Pinned `urllib3==1.26.20` (was `2.6.3` from a prior `pip freeze` that captured the locally upgraded version). `selenium==4.2.0` requires `urllib3~=1.26` (1.x only); the 2.x pin caused CI `pip install` to fail with a dependency conflict.

---

## 2026-07-08

### Fixed CI pa11y failure — scipy missing from requirements.txt and percy version wrong
- `requirements.txt`: Added `scipy==1.15.3` (used by `components/tpm_violin_plot_plotly.py`; omission caused `ModuleNotFoundError` in CI and prevented the app from starting). Downgraded `percy` to `1.1.1` (was `2.0.2` from a previous `pip freeze`; v2 removes `percy.Runner` which `dash[testing]` requires).

### Fixed all MegaLinter errors and suppressed Flask teardown warning in pytest
- `app.py`: Removed unused imports (`plotly.express as px`, `dash.dcc.Graph.Graph`).
- `components/tpm_violin_plot_plotly.py`: Added `# pylint: disable=import-error` and `# type: ignore[import-untyped]` to numpy, pandas, plotly, and scipy imports for MegaLinter Docker compatibility.
- `etl/load.py`: Fixed isort (third-party before first-party); fixed pyright `Decimal`-to-`float` type mismatch with `# type: ignore[arg-type]`; shortened log message to stay within 88-char line limit.
- `migrations/env.py`: Fixed isort (moved `from db.models import Base` to first-party section with blank line separator).
- `migrations/versions/bd35225208f8_widen_fastq_md5_to_text.py`: Reformatted `op.alter_column` calls per black; fixed isort; added `# pylint: disable=no-member` to silence false-positive alembic.op member errors; switched string literals to double-quotes.
- `tests/conftest.py`: Fixed isort and missing blank line before first function (E302).
- `pytest.ini`: Added `filterwarnings` entry to suppress `PytestUnhandledThreadExceptionWarning` from Flask's `process_request_thread` during test server teardown — a known dash[testing] shutdown issue, not a bug in app code.

## 2026-07-08 (original entries below)

### Fixed percy AttributeError breaking dash_duo tests
- `requirements-dev.txt`: Pinned `percy==1.1.1`. dash[testing] uses `percy.Runner` which was removed in percy v2. Without the pin, pip installs the latest percy (2.x), causing `AttributeError: module 'percy' has no attribute 'Runner'` on all browser-driven tests.

### Fixed all MegaLinter linter errors; added pre-commit gate to CLAUDE.md
- `app.py`, `pages/home.py`, `components/navbar.py`, `components/data_utils.py`, `components/tpm_violin_plot_plotly.py`, `pages/charts.py`: Applied black and isort formatting (black prefers expanded function-call style; isort alphabetizes within sections).
- `pages/__init__.py`: Created empty file so mypy resolves `pages.home` without the "source file found twice" error.
- `tests/test_app.py`: Fixed pyright error (`home.layout.children or []`); added blank line between `from dash` and `from pages` imports so isort's first-party/third-party separator is preserved.
- `tests/conftest.py`: Reordered imports — `selenium` (third-party) before `app` (first-party) with blank line separator.
- `.mega-linter.yml`: Added `PYTHON_ISORT_ARGUMENTS` with `-p` flags for first-party modules (`app`, `components`, `config`, `db`, `pages`) because MegaLinter's Docker isort does not reliably pick up `pyproject.toml` `known_first_party`.
- `pyproject.toml`: Added `config` to `known_first_party` so local isort matches Docker isort behavior.
- `CLAUDE.md`: Added pre-commit instruction — run `pytest --headless` and MegaLinter before every commit/push. Added `rm -rf megalinter-reports` reminder and expanded Docker command.

### Fixed pytest tests broken by multi-page app refactor
- `tests/test_app.py`: Updated `test_layout_contains_h1` to check `pages.home.layout` directly instead of `app.layout.children` (H1 now lives in the home page module, not the root layout). Updated `test_graph_renders` to navigate to `/charts` where the `dcc.Graph` lives.

### Fixed WCAG 2.1 AA: missing lang attribute on html element
- `app.py`: Added `app.index_string` to set `lang="en"` on the `<html>` element (WCAG 3.1.1). pa11y-ci now passes with 0 errors.

## 2026-07-07

### Simplified Node.js/pa11y-ci setup instructions
- `CLAUDE.md`: Streamlined the accessibility automated checking section — remove the version-check step and go straight to install, drop the Node.js installer as an alternative (nvm/nvm-windows only), split the two-terminal run steps into separate code blocks.

## 2026-07-01

### Suppress selenium DeprecationWarnings in pytest output
- `pytest.ini`: Added `filterwarnings = ignore::DeprecationWarning:selenium` to silence urllib3 deprecation warnings emitted by selenium internals on every test run.

### Added Windows instructions to accessibility automated checking section
- `CLAUDE.md`: Expanded Node.js install and pa11y-ci run instructions to cover both macOS (nvm) and Windows (nvm-windows + PowerShell venv activation).

### Added Node.js install instructions to accessibility section
- `CLAUDE.md`: Added `node --version` check and nvm-based install instructions before the pa11y-ci local run steps, so developers know how to get Node.js if it is not already present.

## 2026-06-26

### Fixed fastq_md5 column overflow for paired-end reads
- `db/models.py`: Changed `fastq_md5` from `String(32)` to `Text`. Paired-end runs store two MD5 hashes joined by `;` (65 chars), exceeding the original 32-char limit.
- `migrations/versions/bd35225208f8_widen_fastq_md5_to_text.py`: Migration to ALTER the column type.

### Added load_samples ETL function
- `etl/load.py`: Added `load_samples()` — scans `staging/transformed-metadata/**/*_transformed.tsv`, looks up `dataset_id` by bioproject, and inserts new rows into the `sample` table. Idempotent (skips runs already present). Added helper functions `_opt_str`, `_opt_int`, `_opt_datetime`, and `_opt_numrange` to handle type conversion and "NP"/"NA" sentinels. `age_range_lower` + `age_range_upper` TSV columns are combined into a `psycopg2.extras.NumericRange` with closed bounds. Added `# pylint: disable=import-error` for MegaLinter compatibility. `__main__` now runs `load_datasets()` then `load_samples()`.

### Added Sample ORM model and migration
- `db/models.py`: Added `Sample` model — 34 columns matching the TSV schema. Surrogate integer PK; `dataset_id` integer FK to `dataset.id` (indexed); `run` unique constraint. Date columns use `DateTime`, large counts use `BigInteger`, `age_range` uses PostgreSQL `NUMRANGE` (replaces separate lower/upper columns), long URL uses `Text`; all non-key columns nullable.
- `migrations/versions/8e767ddb148f_create_sample_table.py`: Creates `sample` table with `ix_sample_dataset_id` index; downgrade drops both.

### Updated Git conventions to Gitflow-inspired branching model
- `CLAUDE.md`: Replaced single-line branch naming rule with a full branching model section documenting `main`, `develop`, `feature/*`, and `release/*` branches — when to branch, where to merge, reviewer requirements, and the terminal commands for merging a release branch back into `develop`.

## 2026-06-25

### Fixed Cheaha SSH auth — switch from password-auth to keyboard-interactive via Transport
- `etl/download.py`: Cheaha rejects the SSH `password` protocol method and closes the connection, preventing fallback to keyboard-interactive. Fixed by using `paramiko.Transport` directly and calling `transport.auth_interactive()` with a handler that responds to prompts with the user's password. Host key is still verified against `~/.ssh/known_hosts` using `paramiko.HostKeys`. Also fixed pyright errors: `makefile()` returns bytes so output is now decoded with `.decode("utf-8")`; `SFTPClient.from_transport()` can return `None` so a guard was added.

### Added Dataset ORM model, Alembic migration, and ETL load script
- `db/__init__.py`: Added package marker with header comment.
- `db/models.py`: Created `Base` (declarative base) and `Dataset` ORM model with integer surrogate primary key `id` and unique `bioproject` varchar column.
- `db/connection.py`: Implemented `_db_url()`, `engine`, and `SessionLocal` using env vars via `python-dotenv`.
- `alembic.ini`: Initialized Alembic config; URL intentionally left blank (set dynamically in env.py).
- `migrations/env.py`: Configured Alembic environment to read DB URL from env vars and use `Base.metadata` for autogenerate support.
- `migrations/versions/4df4fc616701_create_dataset_table.py`: Initial migration — creates `dataset` table with `id` (integer PK) and `bioproject` (varchar 20, unique, not null).
- `etl/load.py`: New ETL load script — reads `staging/geo_datasets.csv`, upserts bioproject accessions into the `dataset` table, skipping rows already present. Safe to run repeatedly.

### Fixed ETL Cheaha auth — password prompt instead of SSH key
- `etl/download.py`: Replaced SSH key authentication with `getpass.getpass()` interactive password prompt. Cheaha uses username/password rather than SSH key auth. Password is never stored.
- `etl/download.py`: Added `import getpass`; removed `CHEAHA_SSH_KEY` env var usage.
- `.env.example`: Removed `CHEAHA_SSH_KEY` variable; added note that password is prompted at runtime.
- `CLAUDE.md`: Updated Cheaha access instructions to reflect password prompt instead of SSH key.

### Fixed MegaLinter linter failures (pylint/mypy/pyright) caused by Docker SSL errors
- `app.py`: Added `# pylint: disable=import-error` and `# type: ignore[import-untyped]` on third-party imports. MegaLinter's Docker container cannot reach PyPI due to SSL errors, so PRE_COMMANDS fail to install packages; linters then report all third-party imports as unresolvable.
- `etl/download.py`: Added `# pylint: disable=import-error` and `# type: ignore[import-untyped]` on paramiko, requests, and dotenv imports.
- `tests/conftest.py`: Added `# type: ignore[import-untyped]` to selenium import (was missing the suppress comment).
- `tests/test_app.py`: Added `# pylint: disable=import-error` at module level and `# type: ignore[import-untyped]` to the `from dash import html` import inside the test function. All 8 MegaLinter linters now pass ✅.

### Added SQLAlchemy and Alembic
- Installed `sqlalchemy==2.0.51`, `alembic==1.18.5`, and `Mako==1.3.12` (alembic dependency).
- Updated `requirements.txt` via `pip freeze`.

### Fixed CI browser tests — Chrome crashes without display
- `.github/workflows/tests.yml`: Added `--headless` to the pytest command. `ubuntu-latest` runners have no display server; Chrome launched in windowed mode crashes immediately with "session not created: Chrome instance exited".

### Restricted all CI workflows to push events only
- `.github/workflows/accessibility.yml` and `tests.yml`: Changed `on: [push, pull_request]` to `on: [push]`. MegaLinter was already push-only.

## 2026-06-24

### Fixed dash_duo Chrome crash in GitHub Actions CI
- `tests/conftest.py`: Added `pytest_setup_options` hook that passes `--no-sandbox`, `--disable-dev-shm-usage`, and `--disable-setuid-sandbox` to Chrome. GitHub Actions containers do not support Chrome's sandbox, causing all three browser-driven tests to fail with `SessionNotCreatedException`.

### Fixed MegaLinter black/isort formatting conflicts
- `tests/conftest.py`: Collapsed webdriver_manager import to a single 82-char line so black and isort agree without needing to wrap it; removed extraneous blank line between import groups.
- `pyproject.toml`: Added `profile = "black"` to isort config so the two formatters stay compatible going forward.
- `CLAUDE.md`: Updated local linting section to document the full docker command.

### Fixed remaining MegaLinter errors (second pass)
- `tests/conftest.py`: Added `# pylint: disable=import-error` module-level directive and `# type: ignore[import-untyped]` on pytest and webdriver_manager imports — pylint/pyright use isolated environments in MegaLinter and cannot resolve dev-only packages via PRE_COMMANDS.
- `.mega-linter.yml`: Added `PYTHON_BANDIT_FILTER_REGEX_EXCLUDE: "tests/"` — `pyproject.toml` `exclude_dirs` is not read by MegaLinter's bandit runner.
- `pyproject.toml`: Added `[tool.isort] known_first_party` so isort correctly separates first-party app imports from third-party ones with a blank line.

### Fixed MegaLinter errors from test infrastructure addition
- `app.py`, `tests/test_app.py`, `tests/conftest.py`: Applied black and isort formatting.
- `.mega-linter.yml`: Added `pip install -r requirements-dev.txt` to PRE_COMMANDS so pylint and pyright can resolve `pytest` and `webdriver_manager` imports.
- `pyproject.toml`: Added `[tool.bandit] exclude_dirs = ["tests"]` to suppress B101 (assert_used) false positives in pytest test files.

### Fixed ChromeDriver setup and restored lang="en" (caught by test)
Added `webdriver-manager` to `requirements-dev.txt` and wired it into `conftest.py` via `pytest_configure` so ChromeDriver is auto-downloaded when not already in PATH. `test_lang_attribute` revealed that `app.index_string` (which sets `lang="en"`) had been removed — restored it. All 5 tests now pass.

### Set up dash[testing] + pytest infrastructure
Added automated testing with dash[testing] and pytest:
- `requirements-dev.txt` — test dependencies (dash[testing], pytest, pytest-html)
- `tests/conftest.py` — shared `app` fixture
- `tests/test_app.py` — 5 initial tests: server sanity, layout structure, H1 render, graph render, and `lang="en"` WCAG check
- `pytest.ini` — configures testpath and HTML report output
- `.github/workflows/tests.yml` — CI job that installs deps and runs pytest on every push
- Updated `.gitignore` to exclude `test-reports/`
- Updated `CLAUDE.md` with testing conventions, structure, and what-to-test guidance

### Aligned CLAUDE.md accessibility conventions with PR template checklist
- Fixed stale Language section — now correctly documents `app.index_string` as the mechanism for `lang="en"`, not the removed `html.Html()` approach.
- Fixed alt text rule — decorative images must use `alt=""`, not a non-empty value.
- Added focus indicator convention — never remove `outline` without a replacement.
- Added Dynamic content section — Dash callbacks require `role="status"` or `role="alert"` for screen reader announcements.
- Added axe DevTools to the automated checking guidance.

### Added ADA accessibility checklist to PR template
Added a focused WCAG 2.1 AA checklist to `.github/pull_request_template.md` covering automated scans, content (alt text, chart descriptions, contrast), interaction (keyboard nav, focus, labels, skip link), and structure (heading hierarchy, ARIA live regions, lang attribute).

## 2026-06-23

### Fixed WCAG 2.1 AA: Dash debug button has no accessible label
Set `dev_tools_ui=False` in `app.run()` to suppress Dash's debug panel button, which has no text or ARIA label (axe DevTools critical issue). Hot reload and error catching remain active. Removed the `hideElements` workaround from `.pa11yci` since the element no longer renders. Updated CLAUDE.md to document this requirement.

### Fixed pa11y-ci CI failure — Chromium sandbox and Node.js version
- `.pa11yci`: Added `chromeLaunchConfig.args: ["--no-sandbox", "--disable-setuid-sandbox"]` — required for Puppeteer to launch Chromium in GitHub Actions' containerized environment.
- `.github/workflows/accessibility.yml`: Bumped Node.js from 20 (deprecated on Actions) to 22.

### Fixed WCAG 2.1 AA violations found by pa11y-ci
- `app.py`: Added `app.index_string` to set `lang="en"` on the `<html>` element (WCAG 3.1.1).
- `.pa11yci`: Added `hideElements: "#_dash-global-error-container"` to exclude Dash's dev-only debug button, which has no accessible name but is absent in production.

### Fixed pa11y-ci config — renamed to `.pa11yci` and corrected format
pa11y-ci looks for `.pa11yci` by default, not `.pa11yrc.json`. Renamed via `git mv` and restructured config to use the `defaults` key for shared options, which is required by pa11y-ci's config schema. Updated CLAUDE.md reference.

### Set up ADA Title II / WCAG 2.1 AA accessibility linting
Added `pa11y-ci` to test the running Dash app against WCAG 2.1 AA on every push. Created:
- `package.json` — pa11y-ci dev dependency and `npm run a11y` script
- `.pa11yrc.json` — pa11y config targeting WCAG2AA with 2s wait for React rendering
- `.github/workflows/accessibility.yml` — CI job that starts the app and runs pa11y-ci
- Updated `CLAUDE.md` with Dash-specific WCAG 2.1 AA conventions (text alternatives, form labels, heading hierarchy, color contrast, keyboard nav, skip links)
- Updated `.gitignore` to exclude `pa11y-reports/` and `node_modules/`

### Added Git conventions section to CLAUDE.md
Documented branch naming convention: lowercase with dashes, descriptive of functionality.

### Fixed pyright `reportPrivateImportUsage` error in `app.py` (second attempt)
Updated import to `from dash.dcc.Graph import Graph` per pyright's suggested path.

### Fixed pyright `reportPrivateImportUsage` error in `app.py`
Replaced `dcc.Graph` with a direct import of `Graph` from `dash.dcc` to satisfy pyright's public export check. Removed unused `dcc` import.

### Fixed `.gitignore` linter directory name
Changed `linter_logs` to `megalinter-reports` to match the actual directory name generated by MegaLinter.

### Updated CLAUDE.md — startup and changelog instructions
Added instructions telling Claude Code to read `CLAUDE_CHANGELOG.md` at session start and to log all changes after making them.

### Created CLAUDE.md
Initial project documentation file covering layout, run instructions, dependency management, linting, code style, PR process, and database setup.

### Committed .gitignore update
Added `linter_logs` to `.gitignore` under a "Project specific" section.

### Removed `PYTHON_PYLINT_DISABLE_ERRORS` from `.mega-linter.yml`
Re-enabled pylint errors so they will fail CI builds, restoring enforcement of lint quality checks.
