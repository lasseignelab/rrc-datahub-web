# Claude Changelog

A log of changes made by Claude Code in this project, newest first.

---

## 2026-07-08 (third entry)

### Fixed percy AttributeError breaking dash_duo tests
- `requirements-dev.txt`: Pinned `percy==1.1.1`. dash[testing] uses `percy.Runner` which was removed in percy v2. Without the pin, pip installs the latest percy (2.x), causing `AttributeError: module 'percy' has no attribute 'Runner'` on all browser-driven tests.

## 2026-07-08 (second entry)

### Fixed all MegaLinter linter errors; added pre-commit gate to CLAUDE.md
- `app.py`, `pages/home.py`, `components/navbar.py`, `components/data_utils.py`, `components/tpm_violin_plot_plotly.py`, `pages/charts.py`: Applied black and isort formatting (black prefers expanded function-call style; isort alphabetizes within sections).
- `pages/__init__.py`: Created empty file so mypy resolves `pages.home` without the "source file found twice" error.
- `tests/test_app.py`: Fixed pyright error (`home.layout.children or []`); added blank line between `from dash` and `from pages` imports so isort's first-party/third-party separator is preserved.
- `tests/conftest.py`: Reordered imports — `selenium` (third-party) before `app` (first-party) with blank line separator.
- `.mega-linter.yml`: Added `PYTHON_ISORT_ARGUMENTS` with `-p` flags for first-party modules (`app`, `components`, `config`, `db`, `pages`) because MegaLinter's Docker isort does not reliably pick up `pyproject.toml` `known_first_party`.
- `pyproject.toml`: Added `config` to `known_first_party` so local isort matches Docker isort behavior.
- `CLAUDE.md`: Added pre-commit instruction — run `pytest --headless` and MegaLinter before every commit/push. Added `rm -rf megalinter-reports` reminder and expanded Docker command.

## 2026-07-08

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
