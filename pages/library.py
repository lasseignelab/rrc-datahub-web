from dash import html, register_page
import logging
import dash_bootstrap_components as dbc

register_page(__name__, path="/library")

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

layout = html.Div([
    # Dataset Library components will go here
    dbc.Container(
        [
            html.Section(
                [
                    html.H1("Dataset Library"),
                    html.P(
                        (
                            "Browse and explore all available PKD"
                            " research datasets. Use the filters or"
                            " search bar to find datasets based on "
                            "organism, variant, sample type, and more."
                        ),
                    style={"marginBottom": "16px"},
                ),
            ],
            className="section-card",
        ),

    ])
])