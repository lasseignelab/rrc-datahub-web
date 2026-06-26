# Claude Changelog

A log of changes made by Claude Code in this project, newest first.

---

## 2026-06-26

### Updated Git conventions to Gitflow-inspired branching model
- `CLAUDE.md`: Replaced single-line branch naming rule with a full branching model section documenting `main`, `develop`, `feature/*`, and `release/*` branches — when to branch, where to merge, reviewer requirements, and the terminal commands for merging a release branch back into `develop`.

## 2026-06-25 (continued, third)

### Fixed Cheaha SSH auth — switch from password-auth to keyboard-interactive via Transport
- `etl/download.py`: Cheaha rejects the SSH `password` protocol method and closes the connection, preventing fallback to keyboard-interactive. Fixed by using `paramiko.Transport` directly and calling `transport.auth_interactive()` with a handler that responds to prompts with the user's password. Host key is still verified against `~/.ssh/known_hosts` using `paramiko.HostKeys`. Also fixed pyright errors: `makefile()` returns bytes so output is now decoded with `.decode("utf-8")`; `SFTPClient.from_transport()` can return `None` so a guard was added.

## 2026-06-25 (continued, second)

### Added Dataset ORM model, Alembic migration, and ETL load script
- `db/__init__.py`: Added package marker with header comment.
- `db/models.py`: Created `Base` (declarative base) and `Dataset` ORM model with integer surrogate primary key `id` and unique `bioproject` varchar column.
- `db/connection.py`: Implemented `_db_url()`, `engine`, and `SessionLocal` using env vars via `python-dotenv`.
- `alembic.ini`: Initialized Alembic config; URL intentionally left blank (set dynamically in env.py).
- `migrations/env.py`: Configured Alembic environment to read DB URL from env vars and use `Base.metadata` for autogenerate support.
- `migrations/versions/4df4fc616701_create_dataset_table.py`: Initial migration — creates `dataset` table with `id` (integer PK) and `bioproject` (varchar 20, unique, not null).
- `etl/load.py`: New ETL load script — reads `staging/geo_datasets.csv`, upserts bioproject accessions into the `dataset` table, skipping rows already present. Safe to run repeatedly.

## 2026-06-25 (continued)

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

## 2026-06-25

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
