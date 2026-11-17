"""Tests for the About page layout, content files, and in-page navigation."""

import dash_bootstrap_components as dbc
from dash import dcc, html

from app import app
from pages import about


def find_all(node, component_type):
    """Recursively collect every component of component_type under node."""
    found = []
    if isinstance(node, component_type):
        found.append(node)
    children = getattr(node, "children", None)
    if children is None:
        return found
    if not isinstance(children, list):
        children = [children]
    for child in children:
        found.extend(find_all(child, component_type))
    return found


def test_layout_contains_single_h1():
    """About page has exactly one H1 (WCAG heading structure)."""
    h1_elements = find_all(about.layout, html.H1)
    assert len(h1_elements) == 1
    assert h1_elements[0].children == "About the PKD RRC DataHub"


def test_every_section_has_markdown_file():
    """Each slug in SECTIONS has a non-empty markdown file in content/about/."""
    for _, items in about.SECTIONS:
        for slug, _ in items:
            path = about.CONTENT_DIR / f"{slug}.md"
            assert path.is_file(), f"Missing content file: {path}"
            assert path.read_text(encoding="utf-8").strip(), f"Empty: {path}"


def test_markdown_does_not_skip_heading_levels():
    """Markdown bodies sit under an H3, so they must not use #, ## or ###."""
    for _, items in about.SECTIONS:
        for slug, _ in items:
            for line in about._load_markdown(slug).splitlines():
                if line.startswith("#"):
                    level = len(line) - len(line.lstrip("#"))
                    assert level >= 4, f"{slug}.md uses heading level {level}: {line}"


def test_toc_links_point_to_existing_ids():
    """Every 'On this page' link targets an element id present in the layout."""
    ids = {
        component.id
        for component_type in (html.H2, html.H3)
        for component in find_all(about.layout, component_type)
        if getattr(component, "id", None)
    }
    links = find_all(about.layout, html.A)
    assert links, "Table of contents has no links"
    for link in links:
        assert link.href.startswith("#")
        assert link.href[1:] in ids, f"Broken anchor: {link.href}"


def test_markdown_rendered_for_every_section():
    """One dcc.Markdown block is rendered per section item."""
    expected = sum(len(items) for _, items in about.SECTIONS)
    assert len(find_all(about.layout, dcc.Markdown)) == expected


def test_navbar_links_to_about():
    """Navbar includes a link to the About page."""
    from components.navbar import navbar

    nav = navbar()
    hrefs = [link.href for link in find_all(nav, dcc.Link)]
    hrefs += [item.href for item in find_all(nav, dbc.DropdownMenuItem)]
    assert any(href.startswith("/about") for href in hrefs)


def test_about_page_renders(dash_duo):
    """About page H1 is visible in the browser after navigating to /about."""
    dash_duo.start_server(app)
    dash_duo.driver.get(dash_duo.server_url + "/about")
    dash_duo.wait_for_text_to_equal("h1", "About the PKD RRC DataHub")


def test_about_menu_anchors_match_page_groups():
    """Navbar About dropdown links point at the page's H2 group ids."""
    from components.navbar import ABOUT_MENU

    page_ids = {about._group_id(title) for title, _ in about.SECTIONS}
    menu_ids = {anchor for _, anchor, _ in ABOUT_MENU}
    assert menu_ids == page_ids
