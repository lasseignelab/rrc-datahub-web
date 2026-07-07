from dash import Dash, html, page_container
from components.navbar import navbar

app = Dash(__name__, use_pages=True)

app.layout = html.Div([
    navbar(),
    page_container,
])

if __name__ == "__main__":
    app.run(debug=True, dev_tools_ui=False)
