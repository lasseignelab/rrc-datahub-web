from dash import html
from dash_iconify import DashIconify


def feature_card(title, description, icon, color_class, icon_size=42):
    return html.Div(
        className="feature-item",
        children=[
            html.Div(
                className=f"feature-card-icon {color_class}",
                children=DashIconify(
                    icon=icon,
                    width=icon_size,
                ),
            ),
            html.H3(title),
            html.P(description),
        ],
    )