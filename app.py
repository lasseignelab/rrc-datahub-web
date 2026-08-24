import dash
from dash import Dash, html

from components.header import site_header
from components.navbar import navbar

app = Dash(__name__, use_pages=True, suppress_callback_exceptions=True)
server = app.server  # exposed for gunicorn/production serving

app.layout = html.Div(
    className="app-shell",
    children=[
        site_header(),
        navbar(),
        dash.page_container,
    ],
)

if __name__ == "__main__":
    app.run(debug=True)
