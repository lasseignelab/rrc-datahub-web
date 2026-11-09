from dash import html
from dash_iconify import DashIconify


def feature_card(title, description, icon):
    return html.Div(
        className="feature-row",
        children=[
            html.Div(
                className="feature-row-icon",
                children=DashIconify(
                    icon=icon,
                    width=24,
                ),
            ),
            html.H3(title, className="feature-name"),
            html.Div(className="feature-row-divider"),
            html.P(description, className="feature-description"),
        ],
    )
