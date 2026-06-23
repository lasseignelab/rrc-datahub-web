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
requirements.txt    # Pinned Python dependencies
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

Configuration is in [.pa11yrc.json](.pa11yrc.json).

### Dash-specific conventions

**Text alternatives**
- Every `dcc.Graph` must have a descriptive `aria-label` and a `config={"displayModeBar": False}` caption or `html.Figcaption` sibling explaining the data.
- Images embedded via `html.Img` must have a non-empty `alt` attribute.

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
- Modals and dialogs must trap focus while open and return focus on close.

**Language**
- Set the page language: `app = Dash(__name__, suppress_callback_exceptions=True)` and include `html.Html(lang="en")` in the layout, or pass `meta_tags=[{"name": "lang", "content": "en"}]` to the Dash constructor.

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
