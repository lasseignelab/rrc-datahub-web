from dash import dash, html, register_page
import logging
import dash_bootstrap_components as dbc

from components.page_header import create_page_header
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

layout = html.Div(
    [
        html.Div(
            create_page_header(
                title="Dataset Library",
                description=(
                    "Browse and explore all available PKD research datasets. "
                    "Use the filters or search bar to find datasets based on "
                    "organism, variant, sample type, and more."
                ),
            ),
            className="library-header-wrapper",
        ),

        # Main page content - contained
        dbc.Container(
            [
                # Dataset Library components will go here
            ],
            fluid=True,
        ),

        # Footer
        footer(),
    ],
    className="library-page",
)