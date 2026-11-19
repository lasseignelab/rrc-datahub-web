import dash_bootstrap_components as dbc
from dash import html


def create_page_header(title: str, description: str):
    """Create a consistent introduction header for each page."""
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                html.H1(title, className="page-header-title"),
                                html.P(
                                    description,
                                    className="page-header-description",
                                ),
                            ],
                            className="page-header-content",
                        )
                    )
                ]
            )
        ],
        fluid=True,
        className="page-header",
    )
