from dash import dash, html, register_page
import logging
import dash_bootstrap_components as dbc

from components.footer import footer

register_page(__name__, path="/library")

log = logging.getLogger(__name__)

# --- Update these two values whenever a new version ships ---
VERSION = "0.1"
UPDATED = "2026-08-24"
# --------------------------------------------------------------

GITHUB_URL = "https://github.com/lasseignelab/rrc-datahub"


def logo(src, alt, extra_class=""):
    css_class = f"logo {extra_class}".strip()
    return html.Img(src=f"/assets/{src}", alt=alt, className=css_class)

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

    ]),

    
    # ---- Contact, partner logos, and version footer ----
    footer(),
    ],
    className="library-page",
)