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
    links = [
        ("Home", "/"),
        ("Library", "/library"),
        ("Charts", "/charts"),
    ]

    def nav_link(label, href):
        return dcc.Link(
            label,
            href=href,
            className="nav-link",
        )

    return html.Nav(
        [
            # Mobile hamburger menu
            html.Details(
                [
                    html.Summary(
                        html.Span(
                            [
                                html.Span(className="hamburger-line"),
                                html.Span(className="hamburger-line"),
                                html.Span(className="hamburger-line"),
                            ],
                            className="hamburger-icon",
                        ),
                        className="hamburger-button",
                    ),
                    html.Div(
                        [nav_link(label, href) for label, href in links]
                        + [nav_link("About", "/about")],
                        className="mobile-menu-links",
                    ),
                ],
                id="mobile-menu",
                className="mobile-menu",
            ),
            # Brand / wordmark
            dcc.Link(
                [
                    html.Span(
                        "PKD RRC",
                        className="brand-primary",
                    ),
                    html.Span(
                        "DataHub",
                        className="brand-accent",
                    ),
                ],
                href="/",
                className="site-brand",
            ),
            # Desktop navigation
            html.Div(
                [nav_link(label, href) for label, href in links] + [about_dropdown()],
                className="nav-links desktop-nav-links",
            ),
        ],
        className="site-nav",
    )
