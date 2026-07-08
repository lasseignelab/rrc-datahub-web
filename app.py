# pylint: disable=import-error
from dash import Dash, html, page_container  # type: ignore[import-untyped]

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
        navbar(),
        page_container,
    ]
)

if __name__ == "__main__":
    app.run(debug=True, dev_tools_ui=False)
