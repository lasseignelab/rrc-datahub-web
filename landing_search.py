"""
Landing page gene search box.

Flow:
  type gene -> [Search]
    -> resolve_gene() checks it against the real gene list (typo-tolerant)
    -> on success: redirect to the existing metadata-selection tab's route,
       with ?gene=<resolved gene> in the URL
    -> on failure: show an inline error, no redirect

TODO before wiring into your app:
  1. Set EXISTING_TAB_PATH below to the real route your metadata-selection
     tab is registered at (whatever you passed to dash.register_page's
     `path=` for that page).
  2. In that existing page's layout/callback, read the `gene` query param
     from dcc.Location(id="url").search and use it to pre-select/pre-filter
     your gene dropdown. See read_gene_param_example() below for the pattern
     -- adjust to whatever your actual selector's id/callback looks like.
  3. Merge the layout snippet below into your actual landing page's layout
     (this file's `layout` variable is written to drop in directly).
"""
from urllib.parse import urlencode, parse_qs

import dash
from dash import html, dcc, Input, Output, State, callback, no_update

from gene_validate import resolve_gene

# TODO: set this to your real route for the metadata-selection tab
EXISTING_TAB_PATH = "/charts"


layout = html.Div(
    [
        html.H3("Search DataHub"),

        html.Div(
            [
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


# ---------------------------------------------------------------------------
# Example of the receiving side -- adapt and move this into your existing
# metadata-selection tab's page module, don't leave it here.
# ---------------------------------------------------------------------------
def read_gene_param_example():
    """
    Pattern for the existing tab to read `?gene=Pkd1` on load and pre-select
    it in whatever gene dropdown/selector already exists there.

    @callback(
        Output("your-existing-gene-selector-id", "value"),
        Input("url", "search"),   # requires dcc.Location(id="url") on that page
    )
    def prefill_gene_from_url(search):
        if not search:
            return no_update
        params = parse_qs(search.lstrip("?"))
        gene = params.get("gene", [None])[0]
        return gene or no_update
    """
    pass
