from dash import html

# Update these two values whenever a new version ships.
VERSION = "0.1"
UPDATED = "2026-08-24"

GITHUB_URL = "https://github.com/lasseignelab/rrc-datahub"


def logo(src, alt, extra_class=""):
    css_class = f"logo {extra_class}".strip()
    return html.Img(
        src=f"/assets/{src}",
        alt=alt,
        className=css_class,
    )


def footer():
    """Return the shared site footer."""

    return html.Section(
        className="info-panel",
        children=[
            # Left: Contact information
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
                            rel="noopener noreferrer",
                        )
                    ),
                ],
            ),

            # Center: Partner logos
            html.Div(
                className="info-col footer-logos",
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

            # Right: Version information
            html.Div(
                className="info-col meta-col",
                children=[
                    html.P(
                        [
                            "Version ",
                            html.Span(VERSION, className="mono"),
                        ],
                        className="meta-line",
                    ),
                    html.P(
                        [
                            "Updated ",
                            html.Span(UPDATED, className="mono"),
                        ],
                        className="meta-line",
                    ),
                ],
            ),
        ],
    )
