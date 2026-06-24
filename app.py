import plotly.express as px
from dash import Dash, html
from dash.dcc.Graph import Graph

app = Dash(__name__)

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

fig = px.bar(x=["a", "b", "c"], y=[1, 3, 2])

app.layout = html.Div([html.H1("Hello World"), Graph(figure=fig)])

if __name__ == "__main__":
    app.run(debug=True, dev_tools_ui=False)
