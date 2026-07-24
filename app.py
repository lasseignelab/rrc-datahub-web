from dash import Dash, html, page_container

from components.navbar import navbar

app = Dash(__name__, use_pages=True)

app.index_string = """<!DOCTYPE html>
<html lang="en">
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>"""

app.layout = html.Div(
    [
        html.A("Skip to main content", href="#main-content", className="skip-nav"),
        navbar(),
        html.Main(page_container, id="main-content"),
    ]
)

if __name__ == "__main__":
    app.run(debug=True, dev_tools_ui=False)
