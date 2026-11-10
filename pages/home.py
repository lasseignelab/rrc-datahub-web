import dash
from dash import html

from components import landing_search
from components.footer import footer
from components.feature_card import feature_card


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
                            "A shared resource for polycystic kidney disease "
                            "(PKD) transcriptomic data.",
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
            className="about-card",
            children=[
                html.Div(
                    className="about-content",
                    children=[
                        html.Section(
                            className="about-section",
                            children=[
                                html.H2("About the DataHub"),
                                html.H3(
                                    "A simpler way to explore PKD gene expression data.",
                                    className="about-title",
                                ),
                                html.P(
                                    "The PKD RRC DataHub is a free, web-based platform " 
                                    "that makes public polycystic kidney disease (PKD) gene "
                                    "expression data easier "
                                    "to access and analyze. The Datahub's standardized "
                                    "data processing pipeline and user-friendly tools " 
                                    "help researchers find and evaluate datasets without " 
                                    "requiring programming skills or specialized " 
                                    "bioinformatics knowledge.",
                                    className="about-text",
                                ),
                            ],
                        ),
                        html.Div(className="about-divider"),  
                        html.Div(
                            className="about-features",
                            children=[
                                feature_card(
                                    "Search",
                                    "Find genes, datasets, and studies",
                                    "lucide:search",
                                ),
                                feature_card(
                                    "Filter",
                                    "Narrow results by study characteristics",
                                    "lucide:filter",
                                ),
                                feature_card(
                                    "Visualize",
                                    "Explore expression patterns with charts and tables",
                                    "lucide:chart-no-axes-column-increasing",
                                ),
                                feature_card(
                                    "Export",
                                    "Download results for further analysis",
                                    "lucide:download",
                                ),
                            ],
                        ),

                    ],
                ),
            ],
        ),
        # ---- Reusable footer ----
        footer(),
    ],
)
