import dash
from dash import html

from components import data_chat
from components.feature_card import feature_card
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
                html.Div(className="hero-motif", **{"aria-hidden": "true"}),
                # The page's one H1, for screen readers and the heading
                # order; hidden from view so the chat gets the space (the
                # navbar already shows the name).
                html.H1("PKD RRC DataHub", className="visually-hidden"),
                # ---- Data chat (replaces the gene search box) ----
                html.Section(
                    className="search-section",
                    children=[data_chat.layout],
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
                                    "A simpler way to explore PKD datasets.",
                                    className="about-title",
                                ),
                                html.P(
                                    "The PKD RRC DataHub is a free, "
                                    "web-based platform "
                                    "that makes public polycystic "
                                    "kidney disease (PKD) "
                                    "datasets easier to "
                                    "access and analyze. "
                                    "The DataHub's standardized data "
                                    "processing pipeline "
                                    "and user-friendly tools help "
                                    "researchers find and "
                                    "evaluate datasets without "
                                    "requiring programming "
                                    "skills or specialized bioinformatics"
                                    " knowledge.",
                                    className="about-text",
                                ),
                            ],
                        ),
                        html.Div(className="about-divider"),
                        html.Div(
                            className="about-features",
                            children=[
                                feature_card(
                                    "AI Chat",
                                    "Ask questions about the data in plain language",
                                    "lucide:bot-message-square",
                                ),
                                feature_card(
                                    "Filter",
                                    "Narrow results by study characteristics",
                                    "lucide:filter",
                                ),
                                feature_card(
                                    "Visualize",
                                    "Explore results with charts and tables",
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
