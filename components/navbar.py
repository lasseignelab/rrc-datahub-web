import dash_bootstrap_components as dbc
from dash import dcc, html

# About dropdown entries: (label, anchor id on /about, Bootstrap icon class).
# Anchor ids must match the H2 group ids built by pages/about.py
# (_group_id); tests/test_about.py checks that they stay in sync.
ABOUT_MENU = [
    ("Overview", "about-group-overview", "bi-info-circle"),
    ("Using the DataHub", "about-group-using-the-datahub", "bi-question-circle"),
    ("Methods and reuse", "about-group-methods-and-reuse", "bi-journal-code"),
    ("People and support", "about-group-people-and-support", "bi-people"),
]


def about_dropdown():
    """About menu: opens on click (keyboard/touch) and on hover (mouse)."""
    return dbc.DropdownMenu(
        [
            dbc.DropdownMenuItem(
                [
                    html.Span(label),
                    html.I(className=f"bi {icon}", **{"aria-hidden": "true"}),
                ],
                href=f"/about#{anchor}",
                className="about-menu-item",
            )
            for label, anchor, icon in ABOUT_MENU
        ],
        label="About",
        id="about-menu",
        color="link",
        toggleClassName="nav-link about-menu-toggle",
        className="about-menu",
    )


def navbar():
    return html.Nav(
        [
            dcc.Link("Home", href="/", className="nav-link"),
            dcc.Link("Charts", href="/charts", className="nav-link"),
            about_dropdown(),
        ],
        className="site-nav",
    )
