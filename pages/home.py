import dash
from dash import html

from components import landing_search
from components.footer import footer


dash.register_page(__name__, path="/", name="Home")

# --- Update these two values whenever a new version ships ---
VERSION = "0.1"
UPDATED = "2026-08-24"
# --------------------------------------------------------------

GITHUB_URL = "https://github.com/lasseignelab/rrc-datahub"


def logo(src, alt, extra_class=""):
    css_class = f"logo {extra_class}".strip()
    return html.Img(src=dash.get_asset_url(src), alt=alt, className=css_class)


layout = html.Div(
    className="home-page",
    children=[
        # ---- Hero ----
        html.Section(
            [
                html.Div(
                    className="hero-motif",
                    **{"aria-hidden": "true"}
                ),
                html.Section(
                    className="hero",
                    children=[
                        html.H1(
                            [
                                html.Span("PKD RRC", className="brand-primary"),
                                html.Span(" DataHub", className="brand-accent"),
                            ],
                            className="hero-title",
                        ),
                        html.P(
                            "A shared home for polycystic kidney disease "
                            "transcriptomic data.",
                            className="hero-tagline",
                        ),
                    ],
                ),
                # ---- Gene search ----
                html.Section(
                    className="search-section",
                    children=[landing_search.layout],
                ),
            ],
            className="section-card-full-width hero-section",
        ),

        # ---- About ----
        html.Section(
            [
                html.Section(
                    className="about-section",
                    children=[
                        html.H2("Platform Overview"),
                        html.P(
                            "The PKD RRC DataHub is a free, web-based platform that "
                            "streamlines access to public polycystic kidney disease "
                            "(PKD) gene expression data. Every dataset is processed "
                            "through a standardized pipeline, and a point-and-click "
                            "interface lets users search and filter by study "
                            "characteristics and quality metrics without coding or "
                            "bioinformatics expertise. By eliminating the burden of "
                            "locating, processing, and vetting data, the DataHub "
                            "accelerates hypothesis generation for PKD scientists.",
                            className="about-text",
                        ),
                    ],
                ),
            ],
            className="about-card",
        ),

        # ---- Reusable footer ----
        footer(),
    ],
)
