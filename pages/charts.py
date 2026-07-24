# Charts page: TPM violin plot driven by the PostgreSQL database.

import logging

import dash
import pandas as pd
from dash import Input, Output, State, callback, dcc, html

from components.tpm_violin_plot_plotly import plot_tpm_violin_plotly
from db.connection import SessionLocal
from db.models import Dataset, Gene, Sample, SampleGene

dash.register_page(__name__, path="/charts")

log = logging.getLogger(__name__)

_GENE_SEARCH_LIMIT = 50


def _get_datasets() -> list[str]:
    """Return sorted list of bioproject accessions from the database."""
    session = SessionLocal()
    try:
        rows = session.query(Dataset.bioproject).order_by(Dataset.bioproject).all()
        return [r[0] for r in rows]
    finally:
        session.close()


def _search_genes(search: str) -> list[str]:
    """Return up to 50 gene names matching the search prefix.

    All datasets share the same Ensembl annotation, so no dataset filter is
    needed. Querying the gene table directly avoids an expensive join against
    the 21M-row sample_gene table.
    """
    session = SessionLocal()
    try:
        query = session.query(Gene.gene_name).filter(Gene.gene_name.isnot(None))
        if search:
            query = query.filter(Gene.gene_name.ilike(f"{search}%"))
        return [
            r[0]
            for r in query.order_by(Gene.gene_name).limit(_GENE_SEARCH_LIMIT).all()
        ]
    finally:
        session.close()


def _get_genotypes(bioproject: str) -> list[str]:
    """Return sorted list of distinct genotypes for a dataset."""
    session = SessionLocal()
    try:
        rows = (
            session.query(Sample.genotype)
            .join(Dataset, Dataset.id == Sample.dataset_id)
            .filter(Dataset.bioproject == bioproject, Sample.genotype.isnot(None))
            .distinct()
            .order_by(Sample.genotype)
            .all()
        )
        return [r[0] for r in rows]
    finally:
        session.close()


def _get_tpm_data(bioproject: str, gene_name: str) -> pd.DataFrame:
    """Return DataFrame of (genotype, TPM) rows for a dataset and gene."""
    session = SessionLocal()
    try:
        rows = (
            session.query(Sample.genotype, SampleGene.tpm)
            .join(SampleGene, SampleGene.sample_id == Sample.id)
            .join(Gene, Gene.id == SampleGene.gene_id)
            .join(Dataset, Dataset.id == Sample.dataset_id)
            .filter(
                Dataset.bioproject == bioproject,
                Gene.gene_name == gene_name,
                Sample.genotype.isnot(None),
            )
            .all()
        )
        return pd.DataFrame(rows, columns=["genotype", "TPM"])
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Pre-load initial state so dropdowns are populated on first render
# ---------------------------------------------------------------------------

try:
    _datasets = _get_datasets()
except Exception as exc:
    log.warning("Could not load datasets from database: %s", exc)
    _datasets = []

_initial_genes: list[str] = []
_initial_genotypes: list[str] = []

if _datasets:
    try:
        _initial_genes = _search_genes("")
        _initial_genotypes = _get_genotypes(_datasets[0])
    except Exception as exc:
        log.warning("Could not load initial genes/genotypes: %s", exc)


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

layout = html.Div(
    [
        html.H1("TPM Expression"),
        html.Div(
            [
                html.Label("Dataset", htmlFor="dataset-select"),
                dcc.Dropdown(
                    id="dataset-select",
                    options=[{"label": d, "value": d} for d in _datasets],
                    value=_datasets[0] if _datasets else None,
                    clearable=False,
                ),
            ],
            style={"width": "300px", "marginBottom": "16px"},
        ),
        html.Div(
            [
                html.Label("Gene", htmlFor="gene-select"),
                dcc.Dropdown(
                    id="gene-select",
                    options=[{"label": g, "value": g} for g in _initial_genes],
                    value=_initial_genes[0] if _initial_genes else None,
                    clearable=False,
                ),
            ],
            style={"width": "300px", "marginBottom": "16px"},
        ),
        html.Div(
            [
                html.Label("Groups"),
                dcc.Checklist(
                    id="group-select",
                    options=[{"label": g, "value": g} for g in _initial_genotypes],
                    value=_initial_genotypes,
                    inline=True,
                ),
            ],
            style={"marginBottom": "16px"},
        ),
        html.Div(
            [
                html.Label("Statistical test"),
                dcc.RadioItems(
                    id="stat-test",
                    options=[
                        {"label": "None", "value": "none"},
                        {"label": "Mann-Whitney (2 groups)", "value": "mannwhitney"},
                        {
                            "label": "Kruskal-Wallis (3 or more groups)",
                            "value": "kruskal",
                        },
                    ],
                    value="none",
                    inline=True,
                ),
            ],
            style={"marginBottom": "16px"},
        ),
        dcc.Graph(id="violin-plot"),
    ]
)


# ---------------------------------------------------------------------------
# Callback 1: search value -> gene options (server-side filtered)
# ---------------------------------------------------------------------------


@callback(
    Output("gene-select", "options"),
    Input("gene-select", "search_value"),
    State("gene-select", "value"),
)
def filter_gene_options(search, current_gene):
    """Return up to 50 gene names matching the typed prefix.

    Always includes the currently selected gene so it stays visible in the
    dropdown even when it falls outside the search results.
    """
    genes = _search_genes(search or "")
    if current_gene and current_gene not in genes:
        genes = [current_gene] + genes
    return [{"label": g, "value": g} for g in genes]


# ---------------------------------------------------------------------------
# Callback 2: dataset -> reset gene selection + repopulate group checklist
# ---------------------------------------------------------------------------


@callback(
    Output("gene-select", "value"),
    Output("group-select", "options"),
    Output("group-select", "value"),
    Input("dataset-select", "value"),
)
def update_selectors(bioproject):
    """Reset gene and group selections when the dataset changes."""
    if not bioproject:
        return None, [], []

    genes = _search_genes("")
    genotypes = _get_genotypes(bioproject)

    return (
        genes[0] if genes else None,
        [{"label": g, "value": g} for g in genotypes],
        genotypes,
    )


# ---------------------------------------------------------------------------
# Callback 3: gene + groups + stat test -> render plot
# ---------------------------------------------------------------------------


@callback(
    Output("violin-plot", "figure"),
    Input("dataset-select", "value"),
    Input("gene-select", "value"),
    Input("group-select", "value"),
    Input("stat-test", "value"),
)
def update_plot(bioproject, gene, selected_groups, stat_test):
    """Query TPM values for the selected gene and render the violin plot."""
    if not bioproject or not gene or not selected_groups:
        return {}

    df = _get_tpm_data(bioproject, gene)
    if df.empty:
        return {}

    all_genotypes = sorted(df["genotype"].unique())
    df = df[df["genotype"].isin(selected_groups)]

    return plot_tpm_violin_plotly(
        df,
        group_col="genotype",
        group_order=[g for g in all_genotypes if g in selected_groups],
        stat_test=None if stat_test == "none" else stat_test,
        title=gene,
    )
