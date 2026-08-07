# Charts page: TPM violin plot driven by the PostgreSQL database.

import logging
import math
from collections import Counter

import dash
import pandas as pd
from dash import Input, Output, State, callback, clientside_callback, dcc, html
from sqlalchemy import and_, func, or_

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


def _get_all_sexes() -> list[str]:
    """Return sorted list of distinct non-null sex values in the database."""
    session = SessionLocal()
    try:
        rows = (
            session.query(Sample.sex)
            .filter(Sample.sex.isnot(None))
            .distinct()
            .order_by(Sample.sex)
            .all()
        )
        return [r[0] for r in rows]
    finally:
        session.close()


def _get_age_range_bounds() -> tuple[int, int]:
    """Return the (min, max) age in days from all non-null age_range values.

    Uses PostgreSQL lower() and upper() to extract the bounds of the NUMRANGE
    column. Falls back to (0, 365) if no age data exists.
    """
    session = SessionLocal()
    try:
        min_val = (
            session.query(func.min(func.lower(Sample.age_range)))
            .filter(Sample.age_range.isnot(None))
            .scalar()
        )
        max_val = (
            session.query(func.max(func.upper(Sample.age_range)))
            .filter(Sample.age_range.isnot(None))
            .scalar()
        )
        if min_val is None or max_val is None:
            return 0, 365
        return int(min_val), int(max_val)
    finally:
        session.close()


def _get_datasets_by_filters(
    scientific_names: list[str],
    underlying_variants: list[str],
    sample_types: list[str],
    sexes: list[str],
    age_range: tuple[int, int],
    include_unknown_age: bool,
) -> list[str]:
    """Return sorted bioproject accessions matching all active filters.

    A dataset qualifies when it contains at least one sample whose
    scientific_name, underlying_variant, sample_type, and sex are all in
    the respective selected sets AND whose age satisfies the age condition.
    When include_unknown_age is True, samples with a null age_range pass
    the age condition unconditionally.
    """
    min_age, max_age = age_range
    overlap = and_(
        func.lower(Sample.age_range) <= max_age,
        func.upper(Sample.age_range) >= min_age,
    )
    if include_unknown_age:
        age_cond = or_(Sample.age_range.is_(None), overlap)
    else:
        age_cond = and_(Sample.age_range.isnot(None), overlap)
    session = SessionLocal()
    try:
        rows = (
            session.query(Dataset.bioproject)
            .join(Sample, Sample.dataset_id == Dataset.id)
            .filter(
                Sample.scientific_name.in_(scientific_names),
                Sample.underlying_variant.in_(underlying_variants),
                Sample.sample_type.in_(sample_types),
                Sample.sex.in_(sexes),
                age_cond,
            )
            .distinct()
            .order_by(Dataset.bioproject)
            .all()
        )
        return [r[0] for r in rows]
    finally:
        session.close()


def _get_dataset_table(
    scientific_names: list[str],
    underlying_variants: list[str],
    sample_types: list[str],
    sexes: list[str],
    age_range: tuple[int, int],
    include_unknown_age: bool,
) -> list[dict]:
    """Return one summary row per matching bioproject for the dataset table.

    Applies the same filter logic as _get_datasets_by_filters then aggregates
    distinct scientific_name, underlying_variant, sample_type, and sex values
    across all samples in each qualifying bioproject.
    """
    min_age, max_age = age_range
    overlap = and_(
        func.lower(Sample.age_range) <= max_age,
        func.upper(Sample.age_range) >= min_age,
    )
    if include_unknown_age:
        age_cond = or_(Sample.age_range.is_(None), overlap)
    else:
        age_cond = and_(Sample.age_range.isnot(None), overlap)
    session = SessionLocal()
    try:
        matching = [
            r[0]
            for r in (
                session.query(Dataset.bioproject)
                .join(Sample, Sample.dataset_id == Dataset.id)
                .filter(
                    Sample.scientific_name.in_(scientific_names),
                    Sample.underlying_variant.in_(underlying_variants),
                    Sample.sample_type.in_(sample_types),
                    Sample.sex.in_(sexes),
                    age_cond,
                )
                .distinct()
                .order_by(Dataset.bioproject)
                .all()
            )
        ]
        if not matching:
            return []
        samples = (
            session.query(
                Dataset.bioproject,
                Sample.scientific_name,
                Sample.underlying_variant,
                Sample.sample_type,
                Sample.sex,
                func.lower(Sample.age_range),
                func.upper(Sample.age_range),
            )
            .join(Sample, Sample.dataset_id == Dataset.id)
            .filter(Dataset.bioproject.in_(matching))
            .all()
        )
        agg: dict[str, dict] = {
            bp: {
                "scientific_names": Counter(),
                "underlying_variants": Counter(),
                "sample_types": Counter(),
                "sexes": Counter(),
                "age_ranges": Counter(),
            }
            for bp in matching
        }
        for bp, sci, var, stype, sex, age_lo, age_hi in samples:
            if sci:
                agg[bp]["scientific_names"][sci] += 1
            if var:
                agg[bp]["underlying_variants"][var] += 1
            if stype:
                agg[bp]["sample_types"][stype] += 1
            if sex:
                agg[bp]["sexes"][sex] += 1
            if age_lo is not None or age_hi is not None:
                pair = (
                    int(age_lo) if age_lo is not None else None,
                    int(age_hi) if age_hi is not None else None,
                )
                agg[bp]["age_ranges"][pair] += 1

        def _fmt(lo: int | None, hi: int | None) -> str:
            if lo is not None and hi is not None:
                return str(lo) if lo == hi else f"{lo}–{hi}"
            if lo is not None:
                return f"{lo}+"
            return f"–{hi}"

        def _sort_key(pair: tuple) -> tuple:
            lo, hi = pair
            return (
                lo if lo is not None else float("inf"),
                hi if hi is not None else float("inf"),
            )

        return [
            {
                "bioproject": bp,
                "scientific_names": [
                    f"{name} ({cnt})"
                    for name, cnt in sorted(agg[bp]["scientific_names"].items())
                ],
                "underlying_variants": [
                    f"{var} ({cnt})"
                    for var, cnt in sorted(agg[bp]["underlying_variants"].items())
                ],
                "sample_types": [
                    f"{_readable_sample_type(st)} ({cnt})"
                    for st, cnt in sorted(agg[bp]["sample_types"].items())
                ],
                "sexes": [
                    f"{sex} ({cnt})" for sex, cnt in sorted(agg[bp]["sexes"].items())
                ],
                "age_ranges": [
                    f"{_fmt(lo, hi)} ({cnt})"
                    for (lo, hi), cnt in sorted(
                        agg[bp]["age_ranges"].items(), key=lambda x: _sort_key(x[0])
                    )
                ]
                or ["Unknown"],
            }
            for bp in matching
        ]
    finally:
        session.close()


def _build_table_rows(rows: list[dict], selected: str | None) -> list:
    """Build html.Tr list for the dataset selection table."""
    return [
        html.Tr(
            [
                html.Td(
                    html.Button(
                        "",
                        **{
                            "aria-pressed": (
                                "true" if row["bioproject"] == selected else "false"
                            ),
                            "aria-label": f"Select dataset {row['bioproject']}",
                            "data-bp": row["bioproject"],
                        },
                    )
                ),
                html.Td(row["bioproject"]),
                html.Td(", ".join(row["scientific_names"])),
                html.Td(", ".join(row["underlying_variants"])),
                html.Td(", ".join(row["sample_types"])),
                html.Td(", ".join(row["sexes"])),
                html.Td(", ".join(row["age_ranges"])),
            ],
            className=("dataset-row-selected" if row["bioproject"] == selected else ""),
        )
        for row in rows
    ]


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
    _all_sexes = _get_all_sexes()
except Exception as exc:
    log.warning("Could not load sex values from database: %s", exc)
    _all_sexes = []

try:
    _age_min, _age_max = _get_age_range_bounds()
except Exception as exc:
    log.warning("Could not load age range bounds from database: %s", exc)
    _age_min, _age_max = 0, 365

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
                        html.Label("Sex", id="sex-select-label"),
                        dcc.Checklist(
                            id="sex-select",
                            options=[{"label": s, "value": s} for s in _all_sexes],
                            value=_all_sexes,
                            inline=True,
                        ),
                    ],
                    style={"marginBottom": "16px"},
                ),
                html.Div(
                    [
                        html.Label("Age range (days)", htmlFor="age-range-slider"),
                        dcc.RangeSlider(
                            id="age-range-slider",
                            min=_age_min,
                            max=_age_max,
                            step=1,
                            value=[_age_min, _age_max],
                            marks={
                                _age_min: str(_age_min),
                                _age_max: str(_age_max),
                            },
                            tooltip={
                                "placement": "bottom",
                                "always_visible": True,
                            },
                        ),
                        dcc.Checklist(
                            id="include-unknown-age",
                            options=[
                                {
                                    "label": "Include samples with unknown age",
                                    "value": "include",
                                }
                            ],
                            value=["include"],
                            style={"marginTop": "8px"},
                        ),
                    ],
                    # Extra bottom padding so the tooltip doesn't overlap
                    # the checkbox below it.
                    style={"marginBottom": "40px"},
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label("Dataset", id="dataset-table-label"),
                                html.Span(
                                    id="dataset-count",
                                    style={
                                        "marginLeft": "8px",
                                        "color": "#555",
                                        "fontSize": "0.9em",
                                    },
                                ),
                            ],
                            style={"marginBottom": "4px"},
                        ),
                        html.Div(
                            html.Table(
                                [
                                    html.Thead(
                                        html.Tr(
                                            [
                                                html.Th("Select", scope="col"),
                                                html.Th("BioProject ID", scope="col"),
                                                html.Th(
                                                    "Scientific Name (n)",
                                                    scope="col",
                                                ),
                                                html.Th(
                                                    "Underlying Variant (n)",
                                                    scope="col",
                                                ),
                                                html.Th("Sample Type (n)", scope="col"),
                                                html.Th("Sex (n)", scope="col"),
                                                html.Th("Age (days) (n)", scope="col"),
                                            ]
                                        )
                                    ),
                                    html.Tbody(id="dataset-table-body"),
                                ],
                                id="dataset-table",
                                **{"aria-labelledby": "dataset-table-label"},
                            ),
                            style={"height": "280px", "overflowY": "auto"},
                            role="region",
                            tabIndex=0,
                            **{"aria-label": "Dataset selection table"},
                        ),
                        dcc.Store(
                            id="dataset-selected",
                            data=_datasets[0] if _datasets else None,
                        ),
                    ],
                    style={"marginBottom": "16px"},
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
# Callback 1: filter inputs -> rebuild dataset table + update selected dataset
# ---------------------------------------------------------------------------


@callback(
    Output("dataset-table-body", "children"),
    Output("dataset-selected", "data"),
    Output("dataset-count", "children"),
    Input("scientific-name-select", "value"),
    Input("underlying-variant-select", "value"),
    Input("sample-type-select", "value"),
    Input("sex-select", "value"),
    Input("age-range-slider", "value"),
    Input("include-unknown-age", "value"),
    State("dataset-selected", "data"),
)
def filter_datasets(
    selected_names,
    selected_variants,
    selected_types,
    selected_sexes,
    age_range,
    include_unknown_age,
    current_dataset,
):
    """Rebuild the dataset table to show only projects matching all active filters."""
    if not selected_names or not selected_variants or not selected_types:
        return [], None, "0 datasets"

    effective_age = tuple(age_range) if age_range else (_age_min, _age_max)
    rows = _get_dataset_table(
        selected_names,
        selected_variants,
        selected_types,
        selected_sexes or [],
        effective_age,
        bool(include_unknown_age),
    )
    bioprojects = [r["bioproject"] for r in rows]
    selected = (
        current_dataset
        if current_dataset in bioprojects
        else (bioprojects[0] if bioprojects else None)
    )
    n = len(rows)
    count = f"{n} dataset{'s' if n != 1 else ''}"
    return _build_table_rows(rows, selected), selected, count


# ---------------------------------------------------------------------------
# Callback 2: search value -> gene options (server-side filtered)
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
    Input("dataset-selected", "data"),
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
    Input("dataset-selected", "data"),
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
    Input("dataset-selected", "data"),
    Input("gene-select", "value"),
    Input("group-select", "value"),
)
def update_table(bioproject, gene, selected_groups):
    """Build a per-genotype summary table of log10(TPM+1) statistics.

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
    n_samples = len(df)
    n_genotypes = df["genotype"].nunique()

    df["log_tpm"] = df["TPM"].apply(lambda x: math.log10(x + 1))
    summary = (
        df.groupby("genotype")
        .agg(
            Max=("log_tpm", "max"),
            Q3=("log_tpm", lambda x: x.quantile(0.75)),
            Median=("log_tpm", "median"),
            Q1=("log_tpm", lambda x: x.quantile(0.25)),
            Min=("log_tpm", "min"),
        )
        .reset_index()
    )

    return "", [
        html.Caption(
            f"{gene} expression — {n_samples} samples, {n_genotypes} genotype(s)"
        ),
        html.Thead(
            html.Tr(
                [
                    html.Th("Genotype", scope="col"),
                    html.Th("Max log10(TPM+1)", scope="col"),
                    html.Th("Q3 log10(TPM+1)", scope="col"),
                    html.Th("Median log10(TPM+1)", scope="col"),
                    html.Th("Q1 log10(TPM+1)", scope="col"),
                    html.Th("Min log10(TPM+1)", scope="col"),
                ]
            )
        ),
        html.Tbody(
            [
                html.Tr(
                    [
                        html.Td(row["genotype"]),
                        html.Td(f"{row['Max']:.4f}"),
                        html.Td(f"{row['Q3']:.4f}"),
                        html.Td(f"{row['Median']:.4f}"),
                        html.Td(f"{row['Q1']:.4f}"),
                        html.Td(f"{row['Min']:.4f}"),
                    ]
                )
                for _, row in summary.iterrows()
            ]
        ),
    ]
