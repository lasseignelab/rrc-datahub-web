from dash import dcc, html


def navbar():
    return html.Nav(
        [
            dcc.Link("Home", href="/", className="nav-link"),
            dcc.Link("Charts", href="/charts", className="nav-link"),
        ],
        className="site-nav",
    )
