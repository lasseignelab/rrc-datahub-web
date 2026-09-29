# test_components.py
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from components import (
    section_header,
)

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css",
    ],
)

app.layout = dbc.Container([

    html.H2("Component Test Page", className="mt-4 mb-4"),

    # --- 1. section_header ---
    html.H5("1. section_header (no tooltip)", className="text-muted mt-4"),
    section_header("Plain Header"),

    html.H5("2. section_header (with tooltip)", className="text-muted mt-4"),
    section_header(
        "Header With Info Icon",
        tooltip_text="Hover the icon — this text should pop up.",
        header_id="test-header",
    )

], fluid="md", className="pb-5")


if __name__ == "__main__":
    app.run(debug=True, port=8051)