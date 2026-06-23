# Claude Changelog

A log of changes made by Claude Code in this project, newest first.

---

## 2026-06-23

### Updated CLAUDE.md — startup and changelog instructions
Added instructions telling Claude Code to read `CLAUDE_CHANGELOG.md` at session start and to log all changes after making them.



### Created CLAUDE.md
Initial project documentation file covering layout, run instructions, dependency management, linting, code style, PR process, and database setup.

### Committed .gitignore update
Added `linter_logs` to `.gitignore` under a "Project specific" section.

### Removed `PYTHON_PYLINT_DISABLE_ERRORS` from `.mega-linter.yml`
Re-enabled pylint errors so they will fail CI builds, restoring enforcement of lint quality checks.
