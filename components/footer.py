from dash import html

from config import GITHUB_URL, UPDATED, VERSION


# Destination for each partner logo in the footer.
LAB_URL = "https://www.lasseigne.org/"
RRC_URL = "https://www.pkd-rrc.org"
UAB_URL = "https://www.uab.edu/"


def logo(src, alt, extra_class=""):
    css_class = f"logo {extra_class}".strip()
    return html.Img(
        src=f"/assets/{src}",
        alt=alt,
        className=css_class,
    )


def logo_link(src, name, href, extra_class=""):
    """Return a partner logo wrapped in an external link.

    The link's accessible name comes from aria-label so screen readers
    announce the destination and that it opens in a new tab; the image
    itself is decorative inside the link, hence the empty alt text.
    """
    return html.A(
        logo(src, name, extra_class),
        href=href,
        target="_blank",
        rel="noopener noreferrer",
        className=f"logo-link logo-link-{extra_class.removeprefix('logo-')}",
        **{"aria-label": f"{name} (opens in a new tab)"},
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
                    logo_link(
                        "logos/lasseigne_lab_logo.png",
                        "Lasseigne Lab",
                        LAB_URL,
                        "logo-lab",
                    ),
                    logo_link(
                        "logos/rrc_logo.png",
                        "PKD Research Resource Consortium",
                        RRC_URL,
                        "logo-rrc",
                    ),
                    logo_link(
                        "logos/uab_logo.png",
                        "University of Alabama at Birmingham",
                        UAB_URL,
                        "logo-uab",
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
