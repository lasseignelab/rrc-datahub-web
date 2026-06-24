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
requirements.txt        # Pinned production dependencies
requirements-dev.txt    # Test/dev dependencies (pytest, dash[testing])
tests/
  conftest.py           # Shared pytest fixtures
  test_app.py           # Tests for app.py
pytest.ini              # pytest configuration
```

## Running the app

```bash
source venv/bin/activate
python app.py          # dev server at http://localhost:8050 (debug=True)
```

For production:

```bash
gunicorn app:server
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
pytest
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

To approximate CI locally:

```bash
pylint **/*.py
```

Configuration lives in [.mega-linter.yml](.mega-linter.yml).

## Code style

- Follow the team [Coding Guidelines](https://docs.google.com/document/d/1h1hxQGrqnQqo1pAxrrtX1OtjHddRTqtgsgDFSXOQpzk/edit?usp=sharing).
- Meaningful variable and function names; no single-letter names outside loop indices.
- Each file should have a header comment describing its purpose.
- Each function should have a docstring.
- Inline comments explain *why*, not *what*.

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
