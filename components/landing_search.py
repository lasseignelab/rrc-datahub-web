"""
Landing page gene search box.

Flow:
  type gene -> [Search]
    -> resolve_gene() checks it against the real gene list (typo-tolerant)
    -> on success: redirect to the existing metadata-selection tab's route,
       with ?gene=<resolved gene> in the URL
    -> on failure: show an inline error, no redirect
"""
from urllib.parse import urlencode

from dash import html, dcc, Input, Output, State, callback, no_update

from gene_validate import resolve_gene

# TODO: set this to your real route for the metadata-selection tab
EXISTING_TAB_PATH = "/charts"


layout = html.Div(
    [
        html.H3("Search DataHub"),

        html.Div(
            [
                html.Label(
                    "Search by gene name",
                    htmlFor="gene-search-input",
                    style={
                        "position": "absolute",
                        "width": "1px",
                        "height": "1px",
                        "padding": "0",
                        "margin": "-1px",
                        "overflow": "hidden",
                        "clip": "rect(0, 0, 0, 0)",
                        "whiteSpace": "nowrap",
                        "border": "0",
                    },
                ),

                dcc.Input(
                    id="gene-search-input",
                    type="text",
                    placeholder="Search by gene name, e.g. Pkd1",
                    debounce=True,
                    style={
                        "width": "320px",
                        "height": "40px",
                        "fontSize": "18px",
                        "padding": "0 10px",
                    },
                ),

                html.Button(
                    "Search",
                    id="gene-search-submit",
                    n_clicks=0,
                    style={
                        "marginTop": "12px",
                        "padding": "8px 24px",
                        "fontSize": "16px",
                    },
                ),
            ],
            style={
                "display": "flex",
                "flexDirection": "column",
                "alignItems": "center",
            },
        ),

        html.Div(
            id="gene-search-feedback",
            style={
                "marginTop": "8px",
                "textAlign": "center",
            },
        ),

        dcc.Location(
            id="gene-search-redirect",
            refresh=True,
        ),
    ],
    style={
        "textAlign": "center",
    },
)


@callback(
    Output("gene-search-feedback", "children"),
    Output("gene-search-redirect", "href"),
    Input("gene-search-submit", "n_clicks"),
    State("gene-search-input", "value"),
    prevent_initial_call=True,
)
def handle_gene_search(n_clicks, query):
    if not query:
        return "Enter a gene name to search.", no_update

    result = resolve_gene(query)

    if result.error:
        return result.error, no_update

    note = f" (matched from '{result.query}')" if result.corrected else ""
    feedback = f"Found {result.resolved_gene}{note} -- redirecting..."

    redirect_url = f"{EXISTING_TAB_PATH}?{urlencode({'gene': result.resolved_gene})}"
    return feedback, redirect_url
