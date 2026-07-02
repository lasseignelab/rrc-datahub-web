import dash
from dash import html, dcc, callback, Input, Output
import pandas as pd

from components.tpm_violin_plot_plotly import plot_tpm_violin_plotly
from components.tpm_violin_plot import melt_nfcore_tpm
from config import get_available_datasets, dataset_paths

dash.register_page(__name__, path="/charts")

# ---------------------------------------------------------------------------
# Server-side cache
# ---------------------------------------------------------------------------
_cache: dict[str, pd.DataFrame] = {}

datasets = get_available_datasets()


def _load_dataset(accession: str) -> pd.DataFrame:
    """Load and cache a dataset by accession."""
    paths           = dataset_paths(accession)
    tpm_wide        = pd.read_csv(paths["tpm"], sep="\t")
    samplesheet     = pd.read_csv(paths["samples"])
    metadata        = pd.read_csv(paths["metadata"], sep="\t")
    sample_metadata = samplesheet[["sample"]].merge(
        metadata[["run", "genotype"]],
        left_on="sample", right_on="run",
        how="left",
    ).drop(columns="run")

    unmatched = sample_metadata[sample_metadata["genotype"].isna()]["sample"].tolist()
    if unmatched:
        print(f"WARNING: {len(unmatched)} samples have no genotype match: {unmatched}")

    long_df = melt_nfcore_tpm(
        tpm_wide, sample_metadata,
        id_col="gene_name",
        sample_id_col="sample",
        group_col="genotype",
    )
    _cache[accession] = long_df
    return long_df


# ---------------------------------------------------------------------------
# Pre-load the first dataset so dropdowns are populated on initial render
# ---------------------------------------------------------------------------
_initial_genes:  list[str] = []
_initial_groups: list[str] = []

if datasets:
    _df = _load_dataset(datasets[0])
    _initial_genes  = sorted(_df["gene_name"].unique())
    _initial_groups = sorted(_df["genotype"].unique())

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

layout = html.Div([
    html.H1("TPM Expression"),

    html.Div([
        html.Label("Dataset"),
        dcc.Dropdown(
            id="dataset-select",
            options=[{"label": d, "value": d} for d in datasets],
            value=datasets[0] if datasets else None,
            clearable=False,
        ),
    ], style={"width": "300px", "marginBottom": "16px"}),

    html.Div([
        html.Label("Gene"),
        dcc.Dropdown(
            id="gene-select",
            options=[{"label": g, "value": g} for g in _initial_genes],
            value=_initial_genes[0] if _initial_genes else None,
            clearable=False,
        ),
    ], style={"width": "300px", "marginBottom": "16px"}),

    html.Div([
        html.Label("Groups"),
        dcc.Checklist(
            id="group-select",
            options=[{"label": g, "value": g} for g in _initial_groups],
            value=_initial_groups,
            inline=True,
        ),
    ], style={"marginBottom": "16px"}),

    html.Div([
        html.Label("Statistical test"),
        dcc.RadioItems(
            id="stat-test",
            options=[
                {"label": "None",           "value": "none"},
                {"label": "Mann-Whitney",   "value": "mannwhitney"},
                {"label": "Kruskal-Wallis", "value": "kruskal"},
            ],
            value="none",
            inline=True,
        ),
    ], style={"marginBottom": "16px"}),

    dcc.Graph(id="violin-plot"),
])

# ---------------------------------------------------------------------------
# Callback 1: dataset -> populate gene + group dropdowns
# ---------------------------------------------------------------------------

@callback(
    Output("gene-select",  "options"),
    Output("gene-select",  "value"),
    Output("group-select", "options"),
    Output("group-select", "value"),
    Input("dataset-select", "value"),
)
def update_selectors(accession):
    if not accession:
        return [], None, [], []

    long_df = _cache.get(accession) or _load_dataset(accession)

    genes  = sorted(long_df["gene_name"].unique())
    groups = sorted(long_df["genotype"].unique())

    return (
        [{"label": g, "value": g} for g in genes],  genes[0],
        [{"label": g, "value": g} for g in groups], groups,
    )


# ---------------------------------------------------------------------------
# Callback 2: gene + group + stat test -> render plot
# ---------------------------------------------------------------------------

@callback(
    Output("violin-plot", "figure"),
    Input("dataset-select", "value"),
    Input("gene-select",    "value"),
    Input("group-select",   "value"),
    Input("stat-test",      "value"),
)
def update_plot(accession, gene, selected_groups, stat_test):
    if not accession or not gene or not selected_groups:
        return {}
    if accession not in _cache:
        return {}

    long_df    = _cache[accession]
    all_groups = sorted(long_df["genotype"].unique())

    gene_df = long_df[
        (long_df["gene_name"] == gene) &
        (long_df["genotype"].isin(selected_groups))
    ]

    return plot_tpm_violin_plotly(
        gene_df,
        group_col="genotype",
        group_order=[g for g in all_groups if g in selected_groups],
        stat_test=None if stat_test == "none" else stat_test,
        title=gene,
    )
