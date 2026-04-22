from dash import Dash, html, dcc
import plotly.express as px

app = Dash(__name__)

fig = px.bar(x=["a", "b", "c"], y=[1, 3, 2])

app.layout = html.Div([
    html.H1("Hello World"),
    dcc.Graph(figure=fig)
])

if __name__ == "__main__":
    app.run(debug=True)
