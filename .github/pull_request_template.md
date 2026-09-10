## Summary
<!-- Describe the functionality -->

## Author Checklist
- [ ] All of the necessary scripts, dependencies, and inputs have been included
  in this pull request.
- [ ] Only files relevant to this change are included; no temporary, generated,
  or unrelated files are part of this pull request. Use `.gitignore` to prevent
  irrelevant files from accidentally being included.
- [ ] All automated code checks have passed. The "All checks have passed"
  message should show in the GitHub pull request status box above the
  "Merge pull request" button.
- [ ] No merge conflicts exist. Merge conflicts are indicated by the "This
  branch has conflicts that must be resolved" message in the GitHub pull
  request status box above the "Merge pull request" button.
- [ ] Primary and secondary reviewers have been requested to review this
  pull request.

## Self/Peer Review Checklist ([Coding Guidelines](https://docs.google.com/document/d/1h1hxQGrqnQqo1pAxrrtX1OtjHddRTqtgsgDFSXOQpzk/edit?usp=sharing))
- Meaningful variable and function names
- File header comments
- Function comments
- In-line comments summarize logical sections of code by concisely explaining
  why, not what the code is doing.  Avoid excessive or redundant commenting.
- Random seed is set
- Confirm the code performs the intended functionality 

## Accessibility Checklist (ADA Title II / WCAG 2.1 AA)
<!-- Complete if this PR touches any UI, layout, or content. Skip only for back-end/data-only changes. -->

**Automated**
- [ ] pa11y scan passes (`npm run a11y` with app running)
- [ ] No axe DevTools errors in the browser

**Content**
- [ ] All images have meaningful `alt` text (decorative images use `alt=""`)
- [ ] All Plotly charts have a text description or caption explaining the data
- [ ] All Plotly charts have an accessible table of the plotted data that can be toggled to
- [ ] Text contrast meets WCAG AA (4.5:1 normal, 3:1 large text)
- [ ] Information is not conveyed by color alone

**Interaction**
- [ ] All interactive elements are reachable and operable by keyboard alone
- [ ] The application is usable at 400% zoom.
- [ ] The application is usable with a screen reader.
- [ ] Visible focus indicator is present on all focusable elements
- [ ] Every form field has a visible `<label>`
- [ ] Page includes a "Skip to Main Content" link as the first focusable element

**Structure**
- [ ] Page has exactly one `<H1>`; heading levels are not skipped
- [ ] Dash callback updates that change content are announced to screen readers (`role="status"` or `role="alert"`)
- [ ] `<html lang="en">` is set (handled by `app.index_string` — do not remove it)

<!-- How to setup the project before reproducing results? -->

- If you are new to this project, be sure you have followed the "Running the Application Guide - 5. Instructions on Running a Dash + Plotly + PostgreSQL Project" directions from the following document.

https://docs.google.com/document/d/16DTH744lgiW02RznR7p9QZg25xvAtYyclbkeHz9-dlk/edit?usp=sharing

- If you are also writing code for this project, make sure you have committed or stashed work in progress. An alternative is to clone the repository to separate directories for development and code review.
- Open the project in VS Code and run the following commands in a terminal pane.
```
git fetch origin
git checkout <a-branch>
git pull origin <a-branch>

```

Check the "Getting Started" instructions and make sure everything is set up and installed.

[Getting Started](AGENTS.md#getting-started)

Run the database migrations in a terminal window.
```
source venv/bin/activate
alembic upgrade head

```

If not run previously, run the ETL download and load scripts.
```
python -m etl.download
python -m etl.load

```

## Test Functionality 
<!-- How to test the functionality? -->

Start the application and test it in your browser by running the following command in the terminal.
```
source venv/bin/activate
python app.py          # dev server at http://localhost:8050
```