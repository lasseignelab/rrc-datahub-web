# AGENTS.md — rrc-datahub-web

## Table of contents

- [Getting started](#getting-started)
- [Instructions for AI agents](#instructions-for-ai-agents)
- [Project layout](#project-layout)
- [Dependencies](#dependencies)
- [Environment setup](#environment-setup)
- [Database](#database)
- [ETL load script](#etl-load-script)
- [Testing](#testing)
- [Running the app](#running-the-app)
- [Linting (MegaLinter)](#linting-megalinter)
- [Code style](#code-style)
- [Accessibility (ADA Title II / WCAG 2.1 AA)](#accessibility-ada-title-ii--wcag-21-aa)
- [Git conventions](#git-conventions)
- [Pull requests](#pull-requests)

## Getting started

Follow these steps in order to get the project running locally.

**1. Create a virtual environment and install dependencies** → [Dependencies](#dependencies)

**2. Configure environment variables** → [Environment setup](#environment-setup)

**3. Set up the database and run migrations** → [Database](#database)

**4. Download and load source data** → [ETL load script](#etl-load-script)

**5. Verify: run the test suite** → [Testing](#testing)

**6. Start the app** → [Running the app](#running-the-app)

---

## Instructions for AI agents

- At the start of every session, read [AGENTS_CHANGELOG.md](AGENTS_CHANGELOG.md) to understand the recent history of changes in this project.
- After making any change to this project, append an entry to [AGENTS_CHANGELOG.md](AGENTS_CHANGELOG.md) describing what was changed and why. Use the date `YYYY-MM-DD` and group changes under it. Add new entries at the top, below the header. Because multiple agents work in this project, identify yourself in each entry by noting the agent name/model that made the change.
- **Before every commit and push**: run the full test suite (`pytest --headless`), MegaLinter (Docker command below), and pa11y (`npm run a11y` with the app running). All three must pass with zero errors before committing or pushing. Fix any failures first.

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

## Dependencies

Managed with `pip`. The virtualenv lives in `venv/`. After pulling changes:

To install current dependencies:

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

To add a package:

```bash
pip install <package>
pip freeze > requirements.txt
```

## Environment setup

Configuration is loaded from a `.env` file in the project root using `python-dotenv`. This file is gitignored and must never be committed.

To set up your local environment:

```bash
cp .env.example .env
```

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

Environment variables will be filled in as needed in subsequent setup steps. The `GITHUB_TOKEN`, `CHEAHA_*`, and `STAGING_DIR` variables are only required when running the ETL load script (`etl/download.py`). The `DB_*` variables are required for both the app and the ETL load step.

## Database

The app uses PostgreSQL as its primary database. Python connects to it via `psycopg2-binary`, with the SQLAlchemy ORM managing models and queries and Alembic handling schema migrations. Connection credentials are loaded from `.env` at startup and are never committed to version control.

### Installing PostgreSQL

**macOS** — use [Homebrew](https://brew.sh):

```bash
brew install postgresql@16
brew services start postgresql@16
```

**Windows** — download and run the installer from [postgresql.org/download/windows](https://www.postgresql.org/download/windows/). Accept the defaults and note the password you set for the `postgres` superuser.

**Linux (Ubuntu/Debian)**:

```bash
sudo apt-get install postgresql postgresql-contrib
sudo systemctl enable --now postgresql
```

### Creating the database and user

After installing, open a `psql` shell and create a dedicated database and user:

```bash
psql -U $(whoami) -d postgres  # macOS/Linux; Windows: open "SQL Shell (psql)" from Start menu
```

```sql
CREATE USER rrc_user WITH PASSWORD 'yourpassword';
CREATE DATABASE rrc_datahub OWNER rrc_user;
\q
```

### Connecting the app

Populate the `DB_*` variables in `.env` with the values you just created:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=rrc_datahub
DB_USER=rrc_user
DB_PASSWORD=yourpassword
```

Then apply all migrations to create the tables:

```bash
source venv/bin/activate
alembic upgrade head
```

### Query functions

`db/queries.py` holds **shared** query functions — ones used by two or more pages or components. Queries that are only used in one place belong in that page or component file directly; SQLAlchemy's ORM is already an abstraction layer, so routing every query through `queries.py` adds indirection without benefit.

Rule of thumb:
- Query used in one page → write it in that page file.
- Query used in two or more pages → move it to `db/queries.py`.

## ETL load script

The ETL process downloads source data to a local staging directory and (once the load step is implemented) inserts it into the database. Make sure `.env` variables GITHUB_TOKEN and CHEAHA_USER are populated before running.

### GitHub Token
Follow these steps to create a token:
- Navigate to the GitHub user Settings [Credentials](https://github.com/settings/credentials) section.
- Select "Fine-grained personal access tokens".
- Select "Generate new token".
- Fill in the "Token name" field.
- Select "lasseignelab" as the resource owner.
- Choose "Only select repositories" as the "Repository access" option.
- Select "lasseignelab/rrc-datahub" as the repository.
- Click "Add permission" and select "Contents" from the options and leave the permission as "Access: Read-only".
- Click "Generate token" and immediately copy the token or it will be lost.
- Add the token to the GITHUB_TOKEN variable in the `.env` file.

Follow these steps as an administrator to approve a token:
- Navigate to the GitHub lasseignelab organization Settings tab [Pending access tokens](https://github.com/organizations/lasseignelab/settings/personal-access-token-requests) section to approve pending tokens.
- Select and approve the pending tokens.

### Download step

Downloads from three sources into `STAGING_DIR` (default `staging/`):

| Destination | Source |
|---|---|
| `staging/geo_datasets.csv` | `doc/geo_datasets.csv` from `lasseignelab/rrc-datahub` (GitHub) |
| `staging/transformed-metadata/` | `results/transformed-metadata/` from `lasseignelab/rrc-datahub` (GitHub) |
| `staging/tpm/<PRJNA*>/salmon.merged.gene_tpm.tsv` | UAB Cheaha via SSH/SCP |

**Cheaha SSH access** — the script will prompt for your Cheaha password at runtime (it is never stored). The script uses `RejectPolicy` for host-key verification, so the host must already be in your `~/.ssh/known_hosts`:

```bash
ssh-keyscan cheaha.rc.uab.edu >> ~/.ssh/known_hosts
```

```bash
source venv/bin/activate
python -m etl.download
```

The script logs progress to stdout. On success it prints a summary line with the count of metadata files and TPM files downloaded.

### Load step

```bash
source venv/bin/activate
python -m etl.load
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

pa11y-ci requires the Node.js lts version. Make sure it is installed with the following commands:

**macOS** — use [nvm](https://github.com/nvm-sh/nvm).

```bash
# install nvm if needed: https://github.com/nvm-sh/nvm#installing-and-updating
nvm install --lts
nvm use --lts
```

**Windows** — use [nvm-windows](https://github.com/coreybutler/nvm-windows):

```powershell
# install nvm-windows first: https://github.com/coreybutler/nvm-windows#installation--upgrades
nvm install lts
nvm use lts
```

Then run the checker:

**macOS**
```bash
# In one terminal — start the app
source venv/bin/activate && python app.py
```
```bash
# In another terminal — run the checker
npm install
npm run a11y
```

**Windows** (PowerShell)
```powershell
# In one terminal — start the app
venv\Scripts\Activate.ps1
python app.py

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

This project uses a Gitflow-inspired model combined with elements of GitHub Flow. Active branches are `main`, `develop`, `feature/*`, and `release/*`.

### Branch overview

| Branch | Branches from | Merges into | Purpose |
|---|---|---|---|
| `main` | — | — | Stable, released code. Protected; requires two reviewers. |
| `develop` | `main` | — | Integration branch for completed features. Protected; requires one reviewer. |
| `feature/*` | `develop` | `develop` (via PR) | One feature or fix per branch. |
| `release/*` | `develop` | `main` (via PR) + `develop` (via CLI) | Release stabilization; bug fixes only. |

### Rules for each branch type

**`feature/*`**
- Branch from `develop`.
- Name as `feature/<short-description>`, e.g. `feature/add-ada-automation`.
- Merge back to `develop` via pull request. MegaLinter and all CI checks must pass before merge.

**`release/*`**
- Branch from `develop` when a release is ready to stabilize.
- Name as `release/<version>`, e.g. `release/v0.1.0`.
- Only bug fixes may be committed directly to a release branch — no new features.
- Merge to `main` via pull request (two reviewers required).
- After merging to `main`, merge back into `develop` via the terminal:
  ```bash
  git checkout develop
  git merge --no-ff release/vX.Y.Z
  git push
  ```

### Branch naming rules

Branch names must be **lowercase with dashes**. The `feature/` and `release/` prefixes are required for those types.

Good: `feature/add-plotly-graph`, `feature/fix-pyright-imports`, `release/v0.1.0`  
Bad: `DASH-BUILD-V1`, `feature/MyFeature`, `fix1`, `add-plotly-graph` (missing prefix)

## Pull requests

Use the PR template at [.github/pull_request_template.md](.github/pull_request_template.md). All MegaLinter checks must pass before merge. Feature PRs require one reviewer; release and main PRs require two.
