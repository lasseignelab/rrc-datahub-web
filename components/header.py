from dash import html


def site_header():
    return html.Div(
        [
            html.Span("RRC PKD DataHub", className="brand-wordmark"),
            html.Span("Accelerating Discovery in PKD", className="brand-tagline"),
        ],
        className="site-title-bar",
    )
