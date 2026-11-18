# About page: project background, methods, user guide, citation, funding,
# contacts, release history, and future directions.
#
# Page copy lives in content/about/<slug>.md so it can be updated without
# touching layout code. Markdown files must start at "###" headings because
# this module renders the page H1 and the H2 group headings (WCAG heading
# order). Text marked "[PLACEHOLDER: ...]" still needs real content.

from pathlib import Path

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from components.navbar import ABOUT_MENU
from config import DATASET_COUNT, SAMPLE_COUNT, UPDATED, VERSION

dash.register_page(
    __name__, path="/about", name="About", title="About | PKD RRC DataHub"
)

CONTENT_DIR = Path(__file__).resolve().parent.parent / "content" / "about"

# (group heading, [(markdown slug, item heading), ...]) in display order.
# Each slug must match a file in content/about/ and is also the anchor id
# used by the "On this page" navigation.
SECTIONS = [
    (
        "Overview",
        [
            ("overview", "About the DataHub"),
            ("datasets", "Datasets and accessions"),
            ("release-history", "Version and release history"),
        ],
    ),
    (
        "Using the DataHub",
        [
            ("user-guide", "User guide"),
            ("faq", "FAQ and glossary"),
            ("limitations", "Known limitations"),
        ],
    ),
    (
        "Methods and reuse",
        [
            ("methodology", "Research methodology"),
            ("how-to-cite", "How to cite"),
            ("code-availability", "Code and data availability"),
            ("license", "License and terms of use"),
        ],
    ),
    (
        "People and support",
        [
            ("contact", "Team and contact"),
            ("funding", "Funding"),
            ("acknowledgments", "Acknowledgments"),
            ("feedback", "Feedback and issues"),
            ("future-directions", "Future directions"),
        ],
    ),
]


# Sections whose body is shown as a highlighted callout box.
CALLOUT_SLUGS = {"limitations"}

# Group heading icons, shared with the navbar About dropdown and the sidebar.
GROUP_ICONS = {anchor: icon for _, anchor, icon in ABOUT_MENU}


def _group_id(group_title: str) -> str:
    """Return a stable HTML id for a group heading, e.g. 'about-group-overview'."""
    slug = group_title.lower().replace(" ", "-")
    return f"about-group-{slug}"


def _load_markdown(slug: str) -> str:
    """Read the markdown body for one About section from content/about/."""
    return (CONTENT_DIR / f"{slug}.md").read_text(encoding="utf-8")


def _version_badge() -> html.P:
    """Current version line, sourced from config so Home and About agree."""
    return html.P(
        [
            "Current version ",
            html.Span(VERSION, className="mono"),
            " · last updated ",
            html.Span(UPDATED, className="mono"),
        ],
        className="about-version-line",
    )


def _item_block(slug: str, title: str) -> html.Div:
    """Render one H3 subsection with its markdown body."""
    children: list = [html.H3(title, id=slug, className="about-item-heading")]
    # The release history section also shows the live version from config.
    if slug == "release-history":
        children.append(_version_badge())
    markdown_class = "about-markdown"
    if slug in CALLOUT_SLUGS:
        markdown_class += " about-callout"
    children.append(dcc.Markdown(_load_markdown(slug), className=markdown_class))
    return html.Div(children, className="about-item")


def _group_section(group_title: str, items: list[tuple[str, str]]) -> html.Section:
    """Render one H2 group as a section card containing its subsections."""
    heading_id = _group_id(group_title)
    heading = html.H2(
        [
            html.I(
                className=f"bi {GROUP_ICONS.get(heading_id, 'bi-dot')}",
                **{"aria-hidden": "true"},
            ),
            html.Span(group_title),
        ],
        id=heading_id,
        className="about-group-heading",
    )
    back_to_top = html.A(
        [html.I(className="bi bi-arrow-up", **{"aria-hidden": "true"}), "Back to top"],
        href="#about-title",
        className="about-back-to-top",
    )
    return html.Section(
        [heading] + [_item_block(slug, title) for slug, title in items] + [back_to_top],
        className="section-card about-group",
        **{"aria-labelledby": heading_id},
    )


def _stat_tiles() -> html.Ul:
    """Key facts about the current release, shown in the page header."""
    stats = [
        (f"{DATASET_COUNT}", "datasets"),
        (f"{SAMPLE_COUNT}", "samples"),
        (f"v{VERSION}", ["released ", html.Span(UPDATED, className="text-nowrap")]),
    ]
    return html.Ul(
        [
            html.Li(
                [
                    html.Span(value, className="about-stat-value"),
                    html.Span(label, className="about-stat-label"),
                ],
                className="about-stat",
            )
            for value, label in stats
        ],
        className="about-stats",
        **{"aria-label": "Current release at a glance"},
    )


def _table_of_contents() -> html.Nav:
    """In-page navigation listing every group and its subsections."""
    group_items = []
    for group_title, items in SECTIONS:
        anchor = _group_id(group_title)
        group_items.append(
            html.Li(
                [
                    html.A(
                        [
                            html.I(
                                className=f"bi {GROUP_ICONS.get(anchor, 'bi-dot')}",
                                **{"aria-hidden": "true"},
                            ),
                            html.Span(group_title),
                        ],
                        href=f"#{anchor}",
                        className="about-toc-group",
                    ),
                    html.Ul(
                        [
                            html.Li(
                                html.A(
                                    title, href=f"#{slug}", className="about-toc-item"
                                )
                            )
                            for slug, title in items
                        ],
                        className="about-toc-sublist",
                    ),
                ]
            )
        )
    return html.Nav(
        [
            html.H2(
                "On this page", id="about-toc-heading", className="about-toc-title"
            ),
            html.Ul(group_items, className="about-toc-list"),
        ],
        className="section-card about-toc",
        **{"aria-labelledby": "about-toc-heading"},
    )


layout = html.Div(
    [
        dbc.Container(
            [
                html.Section(
                    [
                        html.H1("About the PKD RRC DataHub", id="about-title"),
                        html.P(
                            "Background, methods, usage instructions, citation "
                            "details, and contact information for the PKD RRC "
                            "DataHub.",
                        ),
                        _stat_tiles(),
                    ],
                    className="section-card about-header",
                ),
                # Wide screens: sticky "On this page" sidebar beside the
                # content. Narrow screens: the columns stack.
                dbc.Row(
                    [
                        dbc.Col(
                            _table_of_contents(),
                            lg=3,
                            className="about-toc-col",
                        ),
                        dbc.Col(
                            [_group_section(title, items) for title, items in SECTIONS],
                            lg=9,
                        ),
                    ]
                ),
            ],
            fluid=True,
            className="py-4 narrow-margins about-page",
        ),
    ]
)
