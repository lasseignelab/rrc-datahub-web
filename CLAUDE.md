# CLAUDE.md — rrc-datahub-web

## Instructions for Claude Code

- At the start of every session, read [CLAUDE_CHANGELOG.md](CLAUDE_CHANGELOG.md) to understand the recent history of changes in this project.
- After making any change to this project, append an entry to [CLAUDE_CHANGELOG.md](CLAUDE_CHANGELOG.md) describing what was changed and why. Use the date `YYYY-MM-DD` and group changes under it. Add new entries at the top, below the header.

Dash + Plotly web application for the RRC DataHub. Built in Python, served via Flask/Gunicorn, backed by a PostgreSQL database.

## Project layout

```
app.py              # Dash app entry point
config.py           # App configuration (env vars, constants)
pages/              # Multi-page Dash pages (one file per page)
components/         # Reusable layout components (charts, filters, navbar)
db/
  connection.py     # PostgreSQL connection setup (psycopg2 + python-dotenv)
  queries.py        # SQL query functions
assets/
  style.css         # Global CSS
etl/
  download.py       # ETL download step (GitHub + Cheaha → local staging)
.env.example            # Template for required environment variables
requirements.txt        # Pinned production dependencies
requirements-dev.txt    # Test/dev dependencies (pytest, dash[testing])
tests/
  conftest.py           # Shared pytest fixtures
  test_app.py           # Tests for app.py
pytest.ini              # pytest configuration
```

## Environment setup

Configuration is loaded from a `.env` file in the project root using `python-dotenv`. This file is gitignored and must never be committed.

To set up your local environment:

```bash
cp .env.example .env
```

Then open `.env` and fill in the values for your environment:

| Variable | Description |
|---|---|
| `DB_HOST` | PostgreSQL host |
| `DB_PORT` | PostgreSQL port (default `5432`) |
| `DB_NAME` | Database name |
| `DB_USER` | Database user |
| `DB_PASSWORD` | Database password |
| `GITHUB_TOKEN` | Personal access token with `repo` read scope for `lasseignelab/rrc-datahub` |
| `CHEAHA_HOST` | UAB Cheaha SSH hostname (e.g. `cheaha.rc.uab.edu`) |
| `CHEAHA_USER` | Your Cheaha username |
| `CHEAHA_BASE_PATH` | Remote base path containing `PRJNA*` directories on Cheaha |
| `STAGING_DIR` | Local directory for ETL-downloaded files (default `staging/`) |

The `GITHUB_TOKEN`, `CHEAHA_*`, and `STAGING_DIR` variables are only required when running the ETL load script (`etl/download.py`). The `DB_*` variables are required for both the app and the ETL load step.

## Running the app

```bash
source venv/bin/activate
python app.py          # dev server at http://localhost:8050 (debug=True, dev_tools_ui=False)
```

`dev_tools_ui=False` suppresses Dash's debug panel button, which has no accessible label and violates WCAG 2.1 AA. Hot reload and error catching remain active.

For production:

```bash
gunicorn app:server
```

## ETL load script

The ETL process downloads source data to a local staging directory and (once the load step is implemented) inserts it into the database. Make sure `.env` is populated before running.

### Download step

Downloads from three sources into `STAGING_DIR` (default `staging/`):

| Destination | Source |
|---|---|
| `staging/geo_datasets.csv` | `doc/geo_datasets.csv` from `lasseignelab/rrc-datahub` (GitHub) |
| `staging/transformed-metadata/` | `results/transformed-metadata/` from `lasseignelab/rrc-datahub` (GitHub) |
| `staging/tpm/<PRJNA*>/salmon.merged.gene_tpm.tsv` | UAB Cheaha via SSH/SCP |

```bash
source venv/bin/activate
python -m etl.download
```

The script logs progress to stdout. On success it prints a summary line with the count of metadata files and TPM files downloaded.

**Cheaha SSH access** — the script will prompt for your Cheaha password at runtime (it is never stored). The script uses `RejectPolicy` for host-key verification, so the host must already be in your `~/.ssh/known_hosts`:

```bash
ssh-keyscan cheaha.rc.uab.edu >> ~/.ssh/known_hosts
```

## Dependencies

Managed with `pip`. The virtualenv lives in `venv/`. After pulling changes:

```bash
pip install -r requirements.txt
```

To add a package:

```bash
pip install <package>
pip freeze > requirements.txt
```

## Testing

Tests live in `tests/` and run with pytest. CI runs them on every push via `.github/workflows/tests.yml`.

Install test dependencies (keep separate from `requirements.txt`):

```bash
pip install -r requirements-dev.txt
```

Run tests locally:

```bash
source venv/bin/activate && pytest --headless
```

An HTML report is generated at `test-reports/report.html` after each run (gitignored).

### Test structure

- `tests/conftest.py` — shared fixtures, including the `app` fixture that provides the Dash app to `dash_duo`
- `tests/test_<module>.py` — one test file per app module or page

### What to test

| Type | Tool | What it covers |
|---|---|---|
| Unit | pytest | Callback logic, data transforms, DB query functions |
| Integration | `dash_duo` | Layout renders, component interactions, callback outputs in browser |
| Accessibility | `dash_duo` + `execute_script` | `lang` attribute, ARIA roles on dynamic content |

### Conventions

- Use `dash_duo` fixtures for anything that requires a browser. Use plain pytest for pure Python logic.
- Each `dash_duo` test calls `dash_duo.start_server(app)` as its first line.
- Use `dash_duo.wait_for_element()` and `dash_duo.wait_for_text_to_equal()` — never `time.sleep()`.
- Test file names mirror the module they test: `components/charts.py` → `tests/test_charts.py`.

## Linting (MegaLinter)

CI runs MegaLinter on every push via `.github/workflows/mega-linter.yml`. Only the `PYTHON` linter family is enabled (pylint + ruff). Pylint errors **will** fail the build.

To run MegaLinter locally (matches CI exactly):

```bash
rm -rf megalinter-reports && docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$(pwd)":/tmp/lint \
  oxsecurity/megalinter:v9
```

Always remove `megalinter-reports/` before running — MegaLinter appends to existing logs rather than replacing them, so stale errors from previous runs will appear in the new report.

Reports are written to `megalinter-reports/` (gitignored).

Configuration lives in [.mega-linter.yml](.mega-linter.yml).

## Code style

- Follow the team [Coding Guidelines](https://docs.google.com/document/d/1h1hxQGrqnQqo1pAxrrtX1OtjHddRTqtgsgDFSXOQpzk/edit?usp=sharing).
- Meaningful variable and function names; no single-letter names outside loop indices.
- Each file should have a header comment describing its purpose.
- Each function should have a docstring.
- Inline comments explain *why*, not *what*.

## Accessibility (ADA Title II / WCAG 2.1 AA)

ADA Title II requires public-sector websites to meet WCAG 2.1 AA. All pages and components must comply.

### Automated checking

[pa11y-ci](https://github.com/pa11y/pa11y-ci) runs against the live app on every push via `.github/workflows/accessibility.yml`. Zero violations are required for the build to pass. To run locally:

```bash
# In one terminal — start the app
source venv/bin/activate && python app.py

# In another terminal — run the checker
npm install
npm run a11y
```

Configuration is in [.pa11yci](.pa11yci).

During development, also run [axe DevTools](https://www.deque.com/axe/devtools/) in the browser to catch issues before push.

### Dash-specific conventions

**Text alternatives**
- Every `dcc.Graph` must have a descriptive `aria-label` and a `config={"displayModeBar": False}` caption or `html.Figcaption` sibling explaining the data.
- Images embedded via `html.Img` must have a meaningful `alt` attribute. Decorative images must use `alt=""`.

**Forms and inputs**
- Every `dcc.Input`, `dcc.Dropdown`, `dcc.Slider`, etc. must have an associated `html.Label` using `htmlFor` pointing to the input's `id`.
- Never rely on `placeholder` text alone as a label.

**Heading hierarchy**
- Use exactly one `html.H1` per page. Follow with `H2`, `H3`, etc. in order — do not skip levels.

**Color and contrast**
- Normal text must meet a 4.5:1 contrast ratio against its background (WCAG AA).
- Large text (≥18pt or ≥14pt bold) must meet 3:1.
- Never convey information by color alone — pair color with a label, pattern, or icon.
- Use colorblind-safe palettes for Plotly figures (e.g., `px.colors.qualitative.Safe`).

**Keyboard navigation**
- All interactive components must be reachable and operable via keyboard alone.
- Every focusable element must have a visible focus indicator. Never use `outline: none` without a custom replacement.
- Modals and dialogs must trap focus while open and return focus on close.

**Language**
- The `<html lang="en">` attribute is set via `app.index_string` in `app.py`. Do not remove or replace `app.index_string` without preserving `lang="en"`.

**Dynamic content (Dash callbacks)**
- Callback updates that change visible content must be announced to screen readers. Wrap status messages in an element with `role="status"` (polite) or `role="alert"` (assertive). Dash does not do this automatically.

**Skip navigation**
- Include a "Skip to main content" link as the first focusable element on every page, linking to the `id` of the main content container.

## Git conventions

Branch names must be **lowercase with dashes** and describe the functionality they contain.

Good: `add-plotly-graph`, `fix-pyright-imports`, `setup-db-connection`  
Bad: `DASH-BUILD-V1`, `feature/MyFeature`, `fix1`

## Pull requests

Use the PR template at [.github/pull_request_template.md](.github/pull_request_template.md). All MegaLinter checks must pass before merge. Request both a primary and a secondary reviewer.

## Database

PostgreSQL via `psycopg2-binary`. Connection credentials are loaded from a `.env` file (not committed). Copy `.env.example` if one exists, or set the following variables:

```
DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASSWORD=
```
