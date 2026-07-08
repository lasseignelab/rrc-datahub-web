"""Tests for the main Dash app layout and rendering."""

from app import app


def test_server_is_flask_app():
    """App exposes a Flask server instance."""
    assert app.server is not None


def test_layout_contains_h1():
    """Home page layout includes an H1 element."""
    from dash import html

    from pages import home

    children = home.layout.children or []
    h1_elements = [c for c in children if isinstance(c, html.H1)]
    assert len(h1_elements) == 1
    assert h1_elements[0].children == "Hello World"


def test_heading_renders(dash_duo):
    """H1 is visible in the browser after page load."""
    dash_duo.start_server(app)
    dash_duo.wait_for_text_to_equal("h1", "Hello World")


def test_graph_renders(dash_duo):
    """Plotly violin chart renders in the browser on the charts page."""
    dash_duo.start_server(app)
    dash_duo.driver.get(dash_duo.server_url + "/charts")
    dash_duo.wait_for_element(".js-plotly-plot")


def test_lang_attribute(dash_duo):
    """HTML element has lang attribute set to 'en' (WCAG 3.1.1)."""
    dash_duo.start_server(app)
    lang = dash_duo.driver.execute_script("return document.documentElement.lang")
    assert lang == "en"
