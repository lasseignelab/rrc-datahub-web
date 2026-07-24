from dash import dcc, html


def navbar():
    return html.Nav(
        [
            dcc.Link("Home", href="/", style={"marginRight": "16px"}),
            dcc.Link("Charts", href="/charts", style={"marginRight": "16px"}),
        ],
        style={
            "padding": "12px 24px",
            "borderBottom": "1px solid #ddd",
            "marginBottom": "24px",
        },
        **{"aria-label": "Site navigation"},
    )
