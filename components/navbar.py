from dash import dcc, html


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
                        [
                            nav_link(label, href)
                            for label, href in links
                        ],
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
                [
                    nav_link(label, href)
                    for label, href in links
                ],
                className="nav-links desktop-nav-links",
            ),
        ],
        className="site-nav",
    )
