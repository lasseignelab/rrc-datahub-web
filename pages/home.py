import dash
from components import landing_search
from dash import html

dash.register_page(__name__, path="/", name="RRC PKD DataHub")

# --- Update these two values whenever a new version ships ---
VERSION = "0.1"
UPDATED = "2026-08-24"
# --------------------------------------------------------------

GITHUB_URL = "https://github.com/lasseignelab/rrc-datahub"


def logo(src, alt, extra_class=""):
    css_class = f"logo {extra_class}".strip()
    return html.Img(src=dash.get_asset_url(src), alt=alt, className=css_class)


layout = html.Div(
    className="narrow-margins home-page",
    children=[
        # ---- Hero ----
        html.Section(
            [
                html.Section(
                    className="hero",
                    children=[
                        html.Div(className="hero-motif", **{"aria-hidden": "true"}),
                        html.H1("RRC PKD DataHub", className="hero-title"),
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
        html.Section(
            [
                # ---- About (placeholder copy) ----
                html.Section(
                    className="about-section",
                    children=[
                        html.H2("Platform Overview"),
                        html.P(
                            "The RRC PKD DataHub is a free, web-based platform that "
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
        # ---- Partners & funding ----
        html.Section(
            className="section-card-full-width funding-section",
            children=[
                html.H2("Partners & Funding"),
                html.Div(
                    className="funding-logos",
                    children=[
                        logo(
                            "logos/lasseigne_lab_logo.png",
                            "Lasseigne Lab logo",
                            "logo-lab",
                        ),
                        logo(
                            "logos/uab_logo.png",
                            "University of Alabama at Birmingham logo",
                        ),
                        logo(
                            "logos/rrc_logo.png",
                            "PKD Research Resource Consortium logo",
                        ),
                    ],
                ),
            ],
        ),
        # ---- Single contact/version panel ----
        html.Section(
            className="info-panel",
            children=[
                html.Div(
                    className="info-col contact-col",
                    children=[
                        html.P(
                            "Brittany Lasseigne, PhD",
                            className="contact-name",
                        ),
                        html.P(
                            html.A(
                                "bnp0001@uab.edu",
                                href="mailto:bnp0001@uab.edu",
                            )
                        ),
                        html.P(
                            html.A(
                                "View on GitHub",
                                href=GITHUB_URL,
                                target="_blank",
                            )
                        ),
                    ],
                ),
                html.Div(
                    className="info-col meta-col",
                    children=[
                        html.P(
                            ["Version ", html.Span(VERSION, className="mono")],
                            className="meta-line",
                        ),
                        html.P(
                            ["Updated ", html.Span(UPDATED, className="mono")],
                            className="meta-line",
                        ),
                    ],
                ),
            ],
        ),
    ],
)
