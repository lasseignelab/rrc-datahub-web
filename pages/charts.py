# Charts page: TPM violin plot driven by the PostgreSQL database.

import logging
import math

import dash
import pandas as pd
from dash import Input, Output, State, callback, clientside_callback, dcc, html

from components.tpm_violin_plot_plotly import plot_tpm_violin_plotly
from db.connection import SessionLocal
from db.models import Dataset, Gene, Sample, SampleGene

dash.register_page(__name__, path="/charts")

log = logging.getLogger(__name__)

_GENE_SEARCH_LIMIT = 50


def _get_all_scientific_names() -> list[str]:
    """Return sorted list of distinct non-null scientific_name values in the database.

    Queries the entire sample table so the checklist reflects all organisms.
    """
    session = SessionLocal()
    try:
        rows = (
            session.query(Sample.scientific_name)
            .filter(Sample.scientific_name.isnot(None))
            .distinct()
            .order_by(Sample.scientific_name)
            .all()
        )
        return [r[0] for r in rows]
    finally:
        session.close()


def _get_all_underlying_variants() -> list[str]:
    """Return sorted list of distinct non-null underlying_variant values.

    Queries the entire sample table so the checklist reflects all variants.
    """
    session = SessionLocal()
    try:
        rows = (
            session.query(Sample.underlying_variant)
            .filter(Sample.underlying_variant.isnot(None))
            .distinct()
            .order_by(Sample.underlying_variant)
            .all()
        )
        return [r[0] for r in rows]
    finally:
        session.close()


def _get_all_sample_types() -> list[str]:
    """Return sorted list of distinct non-null sample_type values across all datasets.

    Used only during pre-load; subsequent narrowing is done via callbacks.
    """
    session = SessionLocal()
    try:
        rows = (
            session.query(Sample.sample_type)
            .filter(Sample.sample_type.isnot(None))
            .distinct()
            .order_by(Sample.sample_type)
            .all()
        )
        return [r[0] for r in rows]
    finally:
        session.close()


def _get_datasets_by_filters(
    scientific_names: list[str],
    underlying_variants: list[str],
    sample_types: list[str],
) -> list[str]:
    """Return sorted bioproject accessions matching all three filters.

    A dataset qualifies when it contains at least one sample whose
    scientific_name, underlying_variant, and sample_type are all in the
    respective selected sets.
    """
    session = SessionLocal()
    try:
        rows = (
            session.query(Dataset.bioproject)
            .join(Sample, Sample.dataset_id == Dataset.id)
            .filter(
                Sample.scientific_name.in_(scientific_names),
                Sample.underlying_variant.in_(underlying_variants),
                Sample.sample_type.in_(sample_types),
            )
            .distinct()
            .order_by(Dataset.bioproject)
            .all()
        )
        return [r[0] for r in rows]
    finally:
        session.close()


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
            r[0] for r in query.order_by(Gene.gene_name).limit(_GENE_SEARCH_LIMIT).all()
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


# Override title-casing for values where automatic conversion would be wrong.
# Extend this dict as new sample_type values are added to the database.
_SAMPLE_TYPE_LABELS: dict[str, str] = {
    "iPSC": "iPSC",
    "hiPSC": "hiPSC",
}


def _readable_sample_type(raw: str) -> str:
    """Return a human-readable label for a raw sample_type database value."""
    if raw in _SAMPLE_TYPE_LABELS:
        return _SAMPLE_TYPE_LABELS[raw]
    return raw.replace("_", " ").replace("-", " ").title()


def _get_tpm_data(bioproject: str, gene_name: str) -> pd.DataFrame:
    """Return DataFrame of (genotype, TPM) rows for a dataset and gene."""
    session = SessionLocal()
    try:
        query = (
            session.query(Sample.genotype, SampleGene.tpm)
            .join(SampleGene, SampleGene.sample_id == Sample.id)
            .join(Gene, Gene.id == SampleGene.gene_id)
            .join(Dataset, Dataset.id == Sample.dataset_id)
            .filter(
                Dataset.bioproject == bioproject,
                Gene.gene_name == gene_name,
                Sample.genotype.isnot(None),
            )
        )
        return pd.DataFrame(query.all(), columns=["genotype", "TPM"])
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Pre-load initial state so dropdowns are populated on first render
# ---------------------------------------------------------------------------

try:
    _all_scientific_names = _get_all_scientific_names()
except Exception as exc:
    log.warning("Could not load scientific names from database: %s", exc)
    _all_scientific_names = []

try:
    _all_underlying_variants = _get_all_underlying_variants()
except Exception as exc:
    log.warning("Could not load underlying variants from database: %s", exc)
    _all_underlying_variants = []

try:
    _all_sample_types = _get_all_sample_types()
except Exception as exc:
    log.warning("Could not load sample types from database: %s", exc)
    _all_sample_types = []

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
        html.Section(
            [
                html.H2("Dataset filters", id="dataset-filters-heading"),
                html.Div(
                    [
                        html.Label("Scientific name", id="scientific-name-label"),
                        dcc.Checklist(
                            id="scientific-name-select",
                            options=[
                                {"label": name, "value": name}
                                for name in _all_scientific_names
                            ],
                            value=_all_scientific_names,
                            inline=True,
                        ),
                    ],
                    style={"marginBottom": "16px"},
                ),
                html.Div(
                    [
                        html.Label("Underlying variant", id="underlying-variant-label"),
                        dcc.Checklist(
                            id="underlying-variant-select",
                            options=[
                                {"label": v, "value": v}
                                for v in _all_underlying_variants
                            ],
                            value=_all_underlying_variants,
                            inline=True,
                        ),
                    ],
                    style={"marginBottom": "16px"},
                ),
                html.Div(
                    [
                        html.Label("Sample type", id="sample-type-label"),
                        dcc.Checklist(
                            id="sample-type-select",
                            options=[
                                {"label": _readable_sample_type(st), "value": st}
                                for st in _all_sample_types
                            ],
                            value=_all_sample_types,
                            inline=True,
                        ),
                    ],
                    style={"marginBottom": "16px"},
                ),
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
            ],
            **{"aria-labelledby": "dataset-filters-heading"},
            style={"marginBottom": "32px"},
        ),
        html.Section(
            [
                html.H2("Plot parameters", id="plot-parameters-heading"),
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
                        html.Label("Groups", id="group-select-label"),
                        dcc.Checklist(
                            id="group-select",
                            options=[
                                {"label": g, "value": g} for g in _initial_genotypes
                            ],
                            value=_initial_genotypes,
                            inline=True,
                        ),
                    ],
                    style={"marginBottom": "16px"},
                ),
                html.Div(
                    [
                        html.Label("Statistical test", id="stat-test-label"),
                        dcc.RadioItems(
                            id="stat-test",
                            options=[
                                {"label": "None", "value": "none"},
                                {
                                    "label": "Mann-Whitney (2 groups)",
                                    "value": "mannwhitney",
                                },
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
                html.Div(
                    [
                        html.Button(
                            "Show table",
                            id="toggle-view-btn",
                            style={"marginRight": "8px"},
                            **{"aria-expanded": "false"},
                        ),
                        html.Button(
                            "Download plot as PNG",
                            id="download-png-btn",
                        ),
                        html.Button(
                            "Download table as CSV",
                            id="download-csv-btn",
                            style={"display": "none"},
                        ),
                    ],
                    style={"marginBottom": "8px"},
                ),
                # Polite live region — announces view switches to screen readers.
                html.Div(id="view-status", role="status", className="visually-hidden"),
                html.Div(
                    dcc.Graph(
                        id="violin-plot",
                        config={"responsive": True, "displayModeBar": False},
                        # minHeight prevents the container from collapsing to ~0 px
                        # when figure={} during a callback update, which would cause
                        # the page to reflow and push nearby elements in and out of
                        # the viewport.
                        style={"width": "100%", "minHeight": "450px"},
                    ),
                    id="plot-container",
                ),
                html.Div(
                    [
                        html.P(id="table-status"),
                        html.Table(
                            id="tpm-data-table",
                            **{"aria-label": "TPM expression data"},
                        ),
                    ],
                    id="table-container",
                    style={"display": "none"},
                ),
            ],
            **{"aria-labelledby": "plot-parameters-heading"},
        ),
    ]
)


# ---------------------------------------------------------------------------
# Clientside callback: toggle button -> switch plot / table view
# ---------------------------------------------------------------------------
# Updating style props via React (not direct DOM manipulation) is required so
# that subsequent server callbacks don't cause React's reconciler to reset the
# display back to the layout default.  Button text and aria-expanded are set
# via DOM manipulation inside the function — safe because toggle-view-btn is
# not a callback output and React will not reconcile it.
clientside_callback(
    """
    function(n_clicks) {
        if (!n_clicks) { return window.dash_clientside.no_update; }
        var showTable = n_clicks % 2 === 1;
        var btn = document.getElementById("toggle-view-btn");
        if (btn) {
            btn.setAttribute("aria-expanded", showTable ? "true" : "false");
            btn.textContent = showTable ? "Show plot" : "Show table";
        }
        var statusEl = document.getElementById("view-status");
        if (statusEl) {
            statusEl.textContent = showTable ? "Table view shown." : "Plot view shown.";
        }
        return [
            {"display": showTable ? "none" : ""},
            {"display": showTable ? "" : "none"},
            {"display": showTable ? "none" : ""},
            {"display": showTable ? "" : "none"}
        ];
    }
    """,
    Output("plot-container", "style"),
    Output("table-container", "style"),
    Output("download-png-btn", "style"),
    Output("download-csv-btn", "style"),
    Input("toggle-view-btn", "n_clicks"),
    prevent_initial_call=True,
)


# ---------------------------------------------------------------------------
# Callback 1: scientific name + sample type selections -> filter dataset list
# ---------------------------------------------------------------------------


@callback(
    Output("dataset-select", "options"),
    Output("dataset-select", "value"),
    Input("scientific-name-select", "value"),
    Input("underlying-variant-select", "value"),
    Input("sample-type-select", "value"),
    State("dataset-select", "value"),
)
def filter_datasets(selected_names, selected_variants, selected_types, current_dataset):
    """Narrow the dataset dropdown to projects matching all three filters."""
    if not selected_names or not selected_variants or not selected_types:
        return [], None

    datasets = _get_datasets_by_filters(
        selected_names, selected_variants, selected_types
    )
    options = [{"label": d, "value": d} for d in datasets]
    value = (
        current_dataset
        if current_dataset in datasets
        else (datasets[0] if datasets else None)
    )
    return options, value


# ---------------------------------------------------------------------------
# Callback 3: search value -> gene options (server-side filtered)
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
# Callback 4: dataset -> reset gene selection + repopulate group checklist
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
# Callback 5: gene + groups + stat test -> render plot
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


# ---------------------------------------------------------------------------
# Callback 6: gene + groups -> populate accessible data table
# ---------------------------------------------------------------------------


@callback(
    Output("table-status", "children"),
    Output("tpm-data-table", "children"),
    Input("dataset-select", "value"),
    Input("gene-select", "value"),
    Input("group-select", "value"),
)
def update_table(bioproject, gene, selected_groups):
    """Build an accessible HTML table of per-sample TPM values.

    The table is always populated in the background; visibility is toggled
    client-side by the 'Show table / Show plot' button so there is no
    server round-trip when switching views.

    No-data states are reported via the sibling #table-status paragraph rather
    than an html.Caption inside the table.  A table that contains only a
    caption (no <th> elements) is misidentified as a layout table by axe-core,
    which then flags the caption as a WCAG violation.
    """
    if not bioproject or not gene or not selected_groups:
        return "No data to display. Select a dataset, gene, and groups.", []

    df = _get_tpm_data(bioproject, gene)
    if df.empty:
        return "No expression data found for the current selection.", []

    df = df[df["genotype"].isin(selected_groups)]
    df = df.sort_values(["genotype", "TPM"]).reset_index(drop=True)

    n_samples = len(df)
    n_genotypes = df["genotype"].nunique()

    return "", [
        html.Caption(
            f"{gene} expression — {n_samples} samples, " f"{n_genotypes} genotype(s)"
        ),
        html.Thead(
            html.Tr(
                [
                    html.Th("Genotype", scope="col"),
                    html.Th("TPM", scope="col"),
                    html.Th("log10(TPM + 1)", scope="col"),
                ]
            )
        ),
        html.Tbody(
            [
                html.Tr(
                    [
                        html.Td(row["genotype"]),
                        html.Td(f"{row['TPM']:.4g}"),
                        html.Td(f"{math.log10(row['TPM'] + 1):.4f}"),
                    ]
                )
                for _, row in df.iterrows()
            ]
        ),
    ]
