# Charts page: TPM violin plot driven by the PostgreSQL database.
# flake8: noqa: E501

import logging
import math
from collections import Counter
from urllib.parse import parse_qs

import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, callback, clientside_callback, dcc, html
from sqlalchemy import and_, func, or_

from components.section_header import section_header
from components.tpm_violin_plot_plotly import DEFAULT_COLORS, plot_tpm_violin_plotly
from db.connection import SessionLocal
from db.models import Dataset, Gene, Sample, SampleGene

dash.register_page(__name__, path="/charts")

log = logging.getLogger(__name__)

_GENE_SEARCH_LIMIT = 50
_WILDTYPE_VALUE = "wild-type"


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
    """Return sorted list of distinct known underlying_variant values.

    Excludes null, Not provided, and Not applicable; those are handled by
    include_unknown_variant.

    Queries the entire sample table so the checklist reflects all variants.
    """
    session = SessionLocal()
    try:
        rows = (
            session.query(Sample.underlying_variant)
            .filter(
                Sample.underlying_variant.isnot(None),
                Sample.underlying_variant != "Not provided",
                Sample.underlying_variant != "Not applicable",
                Sample.underlying_variant != _WILDTYPE_VALUE,
            )
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
    """Return sorted list of distinct known sex values, excluding null, Not provided,
    and Not applicable; those are handled by the include_unknown_sex filter.
    """
    session = SessionLocal()
    try:
        rows = (
            session.query(Sample.sex)
            .filter(
                Sample.sex.isnot(None),
                Sample.sex != "Not provided",
                Sample.sex != "Not applicable",
            )
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
    include_unknown_sex: bool,
    include_unknown_variant: bool,
    require_wildtype: bool,
) -> list[str]:
    """Return sorted bioproject accessions matching all active filters.

    A dataset qualifies when it contains at least one sample whose
    scientific_name, underlying_variant, sample_type, and sex are all in
    the respective selected sets AND whose age satisfies the age condition.
    When include_unknown_age is True, samples with a null age_range pass
    the age condition unconditionally. When include_unknown_sex is True,
    samples with a null or 'Not provided' sex also pass the sex condition.
    When include_unknown_variant is True, samples with a null or 'Not
    provided' underlying_variant also pass the variant condition.
    When require_wildtype is True, only datasets that contain at least one
    wild-type sample are included.
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
    if include_unknown_sex:
        sex_cond = or_(
            Sample.sex.in_(sexes),
            Sample.sex.is_(None),
            Sample.sex.in_(["Not provided", "Not applicable"]),
        )
    else:
        sex_cond = Sample.sex.in_(sexes)
    if include_unknown_variant:
        variant_cond = or_(
            Sample.underlying_variant.in_(underlying_variants),
            Sample.underlying_variant.is_(None),
            Sample.underlying_variant.in_(["Not provided", "Not applicable"]),
        )
    else:
        variant_cond = Sample.underlying_variant.in_(underlying_variants)
    session = SessionLocal()
    try:
        rows = (
            session.query(Dataset.bioproject)
            .join(Sample, Sample.dataset_id == Dataset.id)
            .filter(
                Sample.scientific_name.in_(scientific_names),
                variant_cond,
                Sample.sample_type.in_(sample_types),
                sex_cond,
                age_cond,
            )
            .distinct()
            .order_by(Dataset.bioproject)
            .all()
        )
        result = [r[0] for r in rows]
        if require_wildtype:
            wt_bps = {
                r[0]
                for r in session.query(Dataset.bioproject)
                .join(Sample, Sample.dataset_id == Dataset.id)
                .filter(Sample.underlying_variant == _WILDTYPE_VALUE)
                .distinct()
                .all()
            }
            result = [bp for bp in result if bp in wt_bps]
        return result
    finally:
        session.close()


_DAYS_PER_UNIT: dict[str, float] = {
    "days": 1.0,
    "weeks": 7.0,
    "months": 30.44,
    "years": 365.25,
}


def _to_days(value: float, unit: str) -> int:
    """Convert value in the given unit to whole days (rounded)."""
    return round(value * _DAYS_PER_UNIT.get(unit, 1.0))


def _from_days(days: int, unit: str) -> float:
    """Convert days to the given unit, rounded to 1 decimal place."""
    return round(days / _DAYS_PER_UNIT.get(unit, 1.0), 1)


def _days_to_readable(n: int) -> tuple[int, str]:
    """Convert a day count to (value, unit_singular) in the most appropriate unit.

    Thresholds: <14 days → days, <84 days → weeks, <730 days → months, else years.
    """
    if n < 14:
        return n, "day"
    if n < 84:
        return round(n / 7), "week"
    if n < 730:
        return round(n / 30.44), "month"
    return round(n / 365.25), "year"


def _plural(n: int, unit: str) -> str:
    """Return '{n} {unit}' with the unit pluralised when n != 1."""
    return f"{n} {unit if n == 1 else unit + 's'}"


def _fmt(lo: int | None, hi: int | None) -> str:
    """Format a (lower, upper) day-range pair as a human-readable string."""
    if lo is not None and hi is not None:
        if lo == hi:
            return _plural(*_days_to_readable(lo))
        lo_n, lo_u = _days_to_readable(lo)
        hi_n, hi_u = _days_to_readable(hi)
        if lo_u == hi_u:
            return f"{lo_n}–{hi_n} {hi_u if hi_n == 1 else hi_u + 's'}"
        return f"{_plural(lo_n, lo_u)}–{_plural(hi_n, hi_u)}"
    if lo is not None:
        n, u = _days_to_readable(lo)
        return f"{_plural(n, u)}+"
    if hi is not None:
        n, u = _days_to_readable(hi)
        return f"–{_plural(n, u)}"
    return "Not provided"


def _get_dataset_table(
    scientific_names: list[str],
    underlying_variants: list[str],
    sample_types: list[str],
    sexes: list[str],
    age_range: tuple[int, int],
    include_unknown_age: bool,
    include_unknown_sex: bool,
    include_unknown_variant: bool,
    require_wildtype: bool,
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
    if include_unknown_sex:
        sex_cond = or_(
            Sample.sex.in_(sexes),
            Sample.sex.is_(None),
            Sample.sex.in_(["Not provided", "Not applicable"]),
        )
    else:
        sex_cond = Sample.sex.in_(sexes)
    if include_unknown_variant:
        variant_cond = or_(
            Sample.underlying_variant.in_(underlying_variants),
            Sample.underlying_variant.is_(None),
            Sample.underlying_variant.in_(["Not provided", "Not applicable"]),
        )
    else:
        variant_cond = Sample.underlying_variant.in_(underlying_variants)
    session = SessionLocal()
    try:
        matching = [
            r[0]
            for r in (
                session.query(Dataset.bioproject)
                .join(Sample, Sample.dataset_id == Dataset.id)
                .filter(
                    Sample.scientific_name.in_(scientific_names),
                    variant_cond,
                    Sample.sample_type.in_(sample_types),
                    sex_cond,
                    age_cond,
                )
                .distinct()
                .order_by(Dataset.bioproject)
                .all()
            )
        ]
        if require_wildtype:
            wt_bps = {
                r[0]
                for r in session.query(Dataset.bioproject)
                .join(Sample, Sample.dataset_id == Dataset.id)
                .filter(Sample.underlying_variant == _WILDTYPE_VALUE)
                .distinct()
                .all()
            }
            matching = [bp for bp in matching if bp in wt_bps]
        if not matching:
            return []
        samples = (
            session.query(
                Dataset.bioproject,
                Sample.scientific_name,
                Sample.underlying_variant,
                Sample.sample_type,
                Sample.sex,
                Sample.genotype,
                func.lower(Sample.age_range),
                func.upper(Sample.age_range),
                Sample.age_raw,
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
                "genotypes": Counter(),
                "age_ranges": Counter(),
                "age_null_labels": Counter(),
            }
            for bp in matching
        }
        for bp, sci, var, stype, sex, genotype, age_lo, age_hi, age_raw in samples:
            if sci:
                agg[bp]["scientific_names"][sci] += 1
            if var:
                agg[bp]["underlying_variants"][var] += 1
            if stype:
                agg[bp]["sample_types"][stype] += 1
            if sex:
                agg[bp]["sexes"][sex] += 1
            if genotype:
                agg[bp]["genotypes"][genotype] += 1
            if age_lo is not None or age_hi is not None:
                pair = (
                    int(age_lo) if age_lo is not None else None,
                    int(age_hi) if age_hi is not None else None,
                )
                agg[bp]["age_ranges"][pair] += 1
            else:
                label = (
                    age_raw
                    if age_raw and age_raw not in ("Not provided", "")
                    else "Not provided"
                )
                agg[bp]["age_null_labels"][label] += 1

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
                "genotypes": [
                    f"{g} ({cnt})" for g, cnt in sorted(agg[bp]["genotypes"].items())
                ],
                "age_ranges": (
                    [
                        f"{_fmt(lo, hi)} ({cnt})"
                        for (lo, hi), cnt in sorted(
                            agg[bp]["age_ranges"].items(),
                            key=lambda x: _sort_key(x[0]),
                        )
                    ]
                    + [
                        f"{label} ({cnt})"
                        for label, cnt in sorted(agg[bp]["age_null_labels"].items())
                    ]
                )
                or ["Not provided"],
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
                html.Td(", ".join(row["genotypes"])),
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


def _resolve_url_gene(url_search: str | None) -> str | None:
    """Return the gene name from a '?gene=...' URL query string if it
    matches a real gene in the database (case-insensitive exact match),
    else None. Used to let the landing-page search box pre-select a gene
    when it redirects here.
    """
    if not url_search:
        return None
    candidate = parse_qs(url_search.lstrip("?")).get("gene", [None])[0]
    if not candidate:
        return None
    session = SessionLocal()
    try:
        match = (
            session.query(Gene.gene_name)
            .filter(func.lower(Gene.gene_name) == candidate.lower())
            .first()
        )
        return match[0] if match else None
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


def _get_sample_types_for_dataset(bioproject: str) -> list[str]:
    """Return sorted list of distinct non-null sample types for a dataset."""
    session = SessionLocal()
    try:
        rows = (
            session.query(Sample.sample_type)
            .join(Dataset, Dataset.id == Sample.dataset_id)
            .filter(Dataset.bioproject == bioproject, Sample.sample_type.isnot(None))
            .distinct()
            .order_by(Sample.sample_type)
            .all()
        )
        return [r[0] for r in rows]
    finally:
        session.close()


def _get_sexes_for_dataset(bioproject: str) -> list[str]:
    """Return sorted list of distinct non-null sex values for a dataset."""
    session = SessionLocal()
    try:
        rows = (
            session.query(Sample.sex)
            .join(Dataset, Dataset.id == Sample.dataset_id)
            .filter(Dataset.bioproject == bioproject, Sample.sex.isnot(None))
            .distinct()
            .order_by(Sample.sex)
            .all()
        )
        return [r[0] for r in rows]
    finally:
        session.close()


def _get_age_ranges_for_dataset(bioproject: str) -> list[dict]:
    """Return checklist options for distinct age ranges in a dataset.

    Labels match the Age column format in the dataset table. Values encode
    the (lower, upper) day bounds as 'lo:hi'. Null age_range rows are
    grouped by their age_raw label and encoded as 'raw:<label>' so that
    'Not applicable' and 'Not provided' appear as separate options.
    Options are sorted by lower bound then upper bound, with null last.
    """
    session = SessionLocal()
    try:
        rows = (
            session.query(
                func.lower(Sample.age_range),
                func.upper(Sample.age_range),
                Sample.age_raw,
            )
            .join(Dataset, Dataset.id == Sample.dataset_id)
            .filter(Dataset.bioproject == bioproject)
            .distinct()
            .all()
        )
    finally:
        session.close()

    null_labels: set[str] = set()
    pairs: set[tuple[int, int]] = set()
    for age_lo, age_hi, age_raw in rows:
        if age_lo is None and age_hi is None:
            label = (
                age_raw
                if age_raw and age_raw not in ("Not provided", "")
                else "Not provided"
            )
            null_labels.add(label)
        elif age_lo is not None and age_hi is not None:
            pairs.add((int(age_lo), int(age_hi)))

    def _age_sort_key(pair: tuple) -> tuple:
        return (pair[0], pair[1])

    options = [
        {"label": _fmt(lo, hi), "value": f"{lo}:{hi}"}
        for lo, hi in sorted(pairs, key=_age_sort_key)
    ]
    for label in sorted(null_labels):
        options.append({"label": label, "value": f"raw:{label}"})
    return options


# Override title-casing for values where automatic conversion would be wrong.
# Extend this dict as new sample_type values are added to the database.
_SAMPLE_TYPE_LABELS: dict[str, str] = {
    "iPSC": "iPSC",
    "hiPSC": "hiPSC",
}


def _aria_decimal(value: float) -> str:
    """Return a screen-reader-friendly label for a 4-decimal-place float.

    Reads post-decimal digits individually so "1.5683" is announced as
    "1 point 5 6 8 3" rather than "1 point five thousand six hundred...".
    """
    integer_part, decimal_part = f"{value:.4f}".split(".")
    return f"{integer_part} point {' '.join(decimal_part)}"


def _readable_sample_type(raw: str) -> str:
    """Return a human-readable label for a raw sample_type database value."""
    if raw in _SAMPLE_TYPE_LABELS:
        return _SAMPLE_TYPE_LABELS[raw]
    return raw.replace("_", " ").replace("-", " ").title()


def _get_tpm_data(
    bioproject: str,
    gene_name: str,
    sample_types: list[str],
    sexes: list[str],
    age_ranges: list[str],
) -> pd.DataFrame:
    """Return a DataFrame of (genotype, TPM) rows filtered by dataset, gene,
    sample types, sex, and age ranges."""
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
                Sample.sample_type.in_(sample_types),
                Sample.sex.in_(sexes),
            )
        )
        age_conds = []
        for val in age_ranges:
            if val.startswith("raw:"):
                label = val[4:]
                if label == "Not provided":
                    age_conds.append(
                        and_(
                            Sample.age_range.is_(None),
                            or_(
                                Sample.age_raw.is_(None),
                                Sample.age_raw.in_(["", "Not provided"]),
                            ),
                        )
                    )
                else:
                    age_conds.append(
                        and_(
                            Sample.age_range.is_(None),
                            Sample.age_raw == label,
                        )
                    )
            else:
                lo, hi = (int(x) for x in val.split(":"))
                age_conds.append(
                    and_(
                        func.lower(Sample.age_range) == lo,
                        func.upper(Sample.age_range) == hi,
                    )
                )
        if age_conds:
            query = query.filter(or_(*age_conds))
        return pd.DataFrame(query.all(), columns=["genotype", "TPM"])
    finally:
        session.close()


def _get_tpm_range(bioproject: str, gene_name: str) -> tuple[float, float]:
    """Return the global (min, max) of log10(TPM+1) across all samples
    in a dataset for a gene, ignoring plot-parameter filters.

    Used to pin the y-axis so the scale stays fixed while plot filters change.
    Returns (0.0, 1.0) as a safe fallback when no data exists.
    """
    session = SessionLocal()
    try:
        rows = (
            session.query(SampleGene.tpm)
            .join(Gene, Gene.id == SampleGene.gene_id)
            .join(Sample, Sample.id == SampleGene.sample_id)
            .join(Dataset, Dataset.id == Sample.dataset_id)
            .filter(
                Dataset.bioproject == bioproject,
                Gene.gene_name == gene_name,
                Sample.genotype.isnot(None),
                SampleGene.tpm.isnot(None),
            )
            .all()
        )
    finally:
        session.close()
    if not rows:
        return 0.0, 1.0
    values = [math.log10(r[0] + 1) for r in rows]
    return min(values), max(values)


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
_initial_sample_types_for_plot: list[str] = []
_initial_sexes_for_plot: list[str] = []
_initial_age_ranges_for_plot: list[dict] = []

if _datasets:
    try:
        _initial_genes = _search_genes("")
        _initial_genotypes = _get_genotypes(_datasets[0])
        _initial_sample_types_for_plot = _get_sample_types_for_dataset(_datasets[0])
        _initial_sexes_for_plot = _get_sexes_for_dataset(_datasets[0])
        _initial_age_ranges_for_plot = _get_age_ranges_for_dataset(_datasets[0])
    except Exception as exc:
        log.warning("Could not load initial plot parameter options: %s", exc)


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

layout = html.Div(
    [
        dbc.Container(
            [
                dcc.Location(id="url"),
                html.Section(
                    [
                        html.H1("TPM Expression"),
                        html.P(
                            (
                                "Explore gene expression across datasets. Use the "
                                "filters to select a dataset, then choose a gene "
                                "and one or more genotype groups to generate a "
                                "violin plot and summary statistics table of "
                                "log₁₀(TPM + 1) values."
                            ),
                            style={"marginBottom": "16px"},
                        ),
                    ],
                    className="section-card",
                ),
                html.Section(
                    [
                        html.Section(
                            [
                                section_header(
                                    "Dataset Filter",
                                    tooltip_text=(
                                        "Optional inclusion: Include datasets with "
                                        "missing or non-applicable information. "
                                        "Uncheck to exclude them."
                                    ),
                                    header_id="dataset-filter-heading",
                                ),
                                # Row 1: Scientific Name | Sex | Age Range (wider)
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                html.Label(
                                                    "Scientific name",
                                                    id="scientific-name-label",
                                                    className="fw-semibold",
                                                ),
                                                dcc.Dropdown(
                                                    id="scientific-name-select",
                                                    options=[
                                                        {
                                                            "label": name,
                                                            "value": name,
                                                        }
                                                        for name in (
                                                            _all_scientific_names
                                                        )
                                                    ],
                                                    value=_all_scientific_names,
                                                    multi=True,
                                                ),
                                            ],
                                            md=3,
                                        ),
                                        dbc.Col(
                                            [
                                                html.Label(
                                                    "Sex",
                                                    id="sex-select-label",
                                                    className="fw-semibold",
                                                ),
                                                dcc.Dropdown(
                                                    id="sex-select",
                                                    options=[
                                                        {"label": s, "value": s}
                                                        for s in _all_sexes
                                                    ],
                                                    value=_all_sexes,
                                                    multi=True,
                                                ),
                                                dbc.Checklist(
                                                    id="include-unknown-sex",
                                                    options=[
                                                        {
                                                            "label": (
                                                                "Include datasets sex "
                                                                "with not "
                                                                "provided or N/A"
                                                            ),
                                                            "value": "include",
                                                        }
                                                    ],
                                                    value=["include"],
                                                    className="mt-2",
                                                ),
                                            ],
                                            md=3,
                                        ),
                                        dbc.Col(
                                            [
                                                html.Label(
                                                    "Age range",
                                                    className="fw-semibold",
                                                ),
                                                html.Div(
                                                    [
                                                        html.Label(
                                                            "Minimum",
                                                            htmlFor="age-min-input",
                                                            className="visually-hidden",
                                                        ),
                                                        dcc.Input(
                                                            id="age-min-input",
                                                            type="text",
                                                            inputMode="numeric",
                                                            debounce=True,
                                                            value=_age_min,
                                                            style={
                                                                "flex": "1 1 0",
                                                                "minWidth": "0",
                                                            },
                                                        ),
                                                        html.Span(
                                                            "–", className="px-1"
                                                        ),
                                                        html.Label(
                                                            "Maximum",
                                                            htmlFor="age-max-input",
                                                            className="visually-hidden",
                                                        ),
                                                        dcc.Input(
                                                            id="age-max-input",
                                                            type="text",
                                                            inputMode="numeric",
                                                            debounce=True,
                                                            value=_age_max,
                                                            style={
                                                                "flex": "1 1 0",
                                                                "minWidth": "0",
                                                            },
                                                        ),
                                                        html.Label(
                                                            "Unit",
                                                            id="age-unit-label",
                                                            className=(
                                                                "ms-2 fw-semibold "
                                                                "text-nowrap"
                                                            ),
                                                        ),
                                                        dcc.Dropdown(
                                                            id="age-unit",
                                                            options=[
                                                                {
                                                                    "label": "days",
                                                                    "value": "days",
                                                                },
                                                                {
                                                                    "label": "weeks",
                                                                    "value": "weeks",
                                                                },
                                                                {
                                                                    "label": "months",
                                                                    "value": "months",
                                                                },
                                                                {
                                                                    "label": "years",
                                                                    "value": "years",
                                                                },
                                                            ],
                                                            value="days",
                                                            clearable=False,
                                                            style={
                                                                "flex": "1.3 1 0",
                                                                "minWidth": "110px",
                                                            },
                                                        ),
                                                    ],
                                                    className=(
                                                        "d-flex align-items-center "
                                                        "gap-2 mt-1"
                                                    ),
                                                ),
                                                dcc.Store(
                                                    id="age-range-days",
                                                    data=[_age_min, _age_max],
                                                ),
                                                dbc.Checklist(
                                                    id="include-unknown-age",
                                                    options=[
                                                        {
                                                            "label": (
                                                                "Include datasets"
                                                                " with age not "
                                                                "provided or N/A"
                                                            ),
                                                            "value": "include",
                                                        }
                                                    ],
                                                    value=["include"],
                                                    className="mt-2",
                                                ),
                                            ],
                                            md=6,
                                        ),
                                    ],
                                    className="g-3 mb-3",
                                ),
                                # Row 2: Underlying Variant | Sample Type
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                html.Label(
                                                    "Underlying variant",
                                                    id="underlying-variant-label",
                                                    className="fw-semibold",
                                                ),
                                                dcc.Dropdown(
                                                    id="underlying-variant-select",
                                                    options=[
                                                        {
                                                            "label": v,
                                                            "value": v,
                                                        }
                                                        for v in (
                                                            _all_underlying_variants
                                                        )
                                                    ],
                                                    value=_all_underlying_variants,
                                                    multi=True,
                                                ),
                                                dbc.Checklist(
                                                    id="include-unknown-variant",
                                                    options=[
                                                        {
                                                            "label": (
                                                                "Include datasets with "
                                                                "underlying variant "
                                                                "not provided or N/A"
                                                            ),
                                                            "value": "include",
                                                        }
                                                    ],
                                                    value=["include"],
                                                    className="mt-2",
                                                ),
                                                dbc.Checklist(
                                                    id="require-wildtype",
                                                    options=[
                                                        {
                                                            "label": (
                                                                "Only include datasets "
                                                                "with matching controls"
                                                            ),
                                                            "value": "require",
                                                        }
                                                    ],
                                                    value=[],
                                                    className="mt-1",
                                                ),
                                            ],
                                            md=6,
                                        ),
                                        dbc.Col(
                                            [
                                                html.Label(
                                                    "Sample type",
                                                    id="sample-type-label",
                                                    className="fw-semibold",
                                                ),
                                                dcc.Dropdown(
                                                    id="sample-type-select",
                                                    options=[
                                                        {
                                                            "label": (
                                                                _readable_sample_type(
                                                                    st
                                                                )
                                                            ),
                                                            "value": st,
                                                        }
                                                        for st in (_all_sample_types)
                                                    ],
                                                    value=_all_sample_types,
                                                    multi=True,
                                                ),
                                            ],
                                            md=6,
                                        ),
                                    ],
                                    className="g-3 mb-3",
                                ),
                            ],
                            className="section-card",
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        section_header(
                                            "Found Dataset(s)",
                                            header_id="found-dataset-heading",
                                        ),
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
                                                        html.Th(
                                                            "BioProject ID", scope="col"
                                                        ),
                                                        html.Th(
                                                            "Scientific Name (n)",
                                                            scope="col",
                                                        ),
                                                        html.Th(
                                                            "Underlying Variant (n)",
                                                            scope="col",
                                                        ),
                                                        html.Th(
                                                            "Sample Type (n)",
                                                            scope="col",
                                                        ),
                                                        html.Th("Sex (n)", scope="col"),
                                                        html.Th(
                                                            "Groups (n)", scope="col"
                                                        ),
                                                        html.Th("Age (n)", scope="col"),
                                                    ]
                                                )
                                            ),
                                            html.Tbody(id="dataset-table-body"),
                                        ],
                                        id="dataset-table",
                                        **{"aria-labelledby": "dataset-table-label"},
                                    ),
                                    id="dataset-table-wrapper",
                                    style={"height": "280px", "overflowY": "scroll"},
                                    role="region",
                                    tabIndex=0,
                                    **{"aria-label": "Dataset selection table"},
                                ),
                                dcc.Store(
                                    id="dataset-selected",
                                    data=_datasets[0] if _datasets else None,
                                ),
                                dcc.Store(id="url-gene-applied", data=False),
                            ],
                            className="section-card",
                            style={"marginBottom": "16px"},
                        ),
                    ],
                    className="section-card",
                    **{"aria-labelledby": "dataset-filters-heading"},
                    style={"marginBottom": "32px"},
                ),
                html.Section(
                    [
                        html.Section(
                            [
                                section_header(
                                    "Edit Plot Parameters",
                                    tooltip_text="Edit the plot parameters for "
                                    "the previously selected dataset "
                                    "to customize the plot or table.",
                                    header_id="edit-plot-parameters-heading",
                                ),
                                # Row 1: Gene | Group | Sample Type
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                html.Label(
                                                    "Gene",
                                                    htmlFor="gene-select",
                                                    className="fw-semibold",
                                                ),
                                                dcc.Dropdown(
                                                    id="gene-select",
                                                    options=[
                                                        {"label": g, "value": g}
                                                        for g in _initial_genes
                                                    ],
                                                    value=(
                                                        _initial_genes[0]
                                                        if _initial_genes
                                                        else None
                                                    ),
                                                    clearable=False,
                                                ),
                                            ],
                                            md=4,
                                        ),
                                        dbc.Col(
                                            [
                                                html.Label(
                                                    "Groups",
                                                    id="group-select-label",
                                                    className="fw-semibold",
                                                ),
                                                dcc.Dropdown(
                                                    id="group-select",
                                                    options=[
                                                        {"label": g, "value": g}
                                                        for g in _initial_genotypes
                                                    ],
                                                    value=_initial_genotypes,
                                                    multi=True,
                                                ),
                                            ],
                                            md=4,
                                        ),
                                        dbc.Col(
                                            [
                                                html.Label(
                                                    "Sample type",
                                                    id="plot-sample-type-label",
                                                    className="fw-semibold",
                                                ),
                                                dcc.Dropdown(
                                                    id="plot-sample-type-select",
                                                    options=[
                                                        {
                                                            "label": _readable_sample_type(
                                                                st
                                                            ),
                                                            "value": st,
                                                        }
                                                        for st in (
                                                            _initial_sample_types_for_plot
                                                        )
                                                    ],
                                                    value=(
                                                        _initial_sample_types_for_plot
                                                    ),
                                                    multi=True,
                                                ),
                                            ],
                                            md=4,
                                        ),
                                    ],
                                    className="g-3 mb-3",
                                ),
                                # Row 2: Sex | Age | Statistical Test
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                html.Label(
                                                    "Sex",
                                                    id="plot-sex-label",
                                                    className="fw-semibold",
                                                ),
                                                dcc.Dropdown(
                                                    id="plot-sex-select",
                                                    options=[
                                                        {"label": s, "value": s}
                                                        for s in _initial_sexes_for_plot
                                                    ],
                                                    value=_initial_sexes_for_plot,
                                                    multi=True,
                                                ),
                                            ],
                                            md=4,
                                        ),
                                        dbc.Col(
                                            [
                                                html.Label(
                                                    "Age",
                                                    id="plot-age-label",
                                                    className="fw-semibold",
                                                ),
                                                dcc.Dropdown(
                                                    id="plot-age-select",
                                                    options=(
                                                        _initial_age_ranges_for_plot
                                                    ),
                                                    value=[
                                                        opt["value"]
                                                        for opt in (
                                                            _initial_age_ranges_for_plot
                                                        )
                                                    ],
                                                    multi=True,
                                                ),
                                            ],
                                            md=4,
                                        ),
                                        dbc.Col(
                                            [
                                                html.Label(
                                                    "Statistical test",
                                                    id="stat-test-label",
                                                    className="fw-semibold",
                                                ),
                                                dcc.Dropdown(
                                                    id="stat-test",
                                                    options=[
                                                        {
                                                            "label": "None",
                                                            "value": "none",
                                                        },
                                                        {
                                                            "label": (
                                                                "Mann-Whitney "
                                                                "(2 groups)"
                                                            ),
                                                            "value": "mannwhitney",
                                                        },
                                                        {
                                                            "label": (
                                                                "Kruskal-Wallis ("
                                                                "3 or more groups)"
                                                            ),
                                                            "value": "kruskal",
                                                        },
                                                    ],
                                                    value="none",
                                                ),
                                            ],
                                            md=4,
                                        ),
                                    ],
                                    className="g-3 mb-3",
                                ),
                            ],
                            className="section-card",
                        ),
                        html.Div(
                            [
                                dbc.Button(
                                    "Show table",
                                    id="toggle-view-btn",
                                    className="me-2 btn-dark-gray",
                                ),
                                dbc.Button(
                                    "Download plot as PNG",
                                    id="download-png-btn",
                                    className="me-2 btn-dark-gray",
                                ),
                                dbc.Button(
                                    "Download table as CSV",
                                    id="download-csv-btn",
                                    className="me-2 btn-download",
                                    style={"display": "none"},
                                ),
                            ],
                            className="my-4 d-flex justify-content-center",
                        ),
                        html.Section(
                            [
                                # Polite live region — announces view switches
                                # to screen readers.
                                html.Div(
                                    id="view-status",
                                    role="status",
                                    className="visually-hidden",
                                ),
                                # Filename prefix for downloads — written
                                # by update_plot, read by JS.
                                html.Div(id="download-meta", style={"display": "none"}),
                                html.Div(
                                    dcc.Graph(
                                        id="violin-plot",
                                        config={
                                            "responsive": True,
                                            "displayModeBar": False,
                                        },
                                        # minHeight prevents collapsing.
                                        # It also prevents reflow when figure={}
                                        # during a callback update.
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
                            className="section-card",
                        ),
                    ],
                    className="section-card",
                    **{"aria-labelledby": "plot-parameters-heading"},
                ),
            ],
            fluid=True,
            className="py-4 narrow-margins",
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
    Input("include-unknown-variant", "value"),
    Input("require-wildtype", "value"),
    Input("sample-type-select", "value"),
    Input("sex-select", "value"),
    Input("include-unknown-sex", "value"),
    Input("age-range-days", "data"),
    Input("include-unknown-age", "value"),
    State("dataset-selected", "data"),
)
def filter_datasets(
    selected_names,
    selected_variants,
    include_unknown_variant,
    require_wildtype,
    selected_types,
    selected_sexes,
    include_unknown_sex,
    age_days,
    include_unknown_age,
    current_dataset,
):
    """Rebuild the dataset table to show only projects matching all active filters."""
    variants_exhausted = not selected_variants and not bool(include_unknown_variant)
    if not selected_names or variants_exhausted or not selected_types:
        return [], None, "0 datasets"

    effective_age = (
        (int(age_days[0]), int(age_days[1])) if age_days else (_age_min, _age_max)
    )
    rows = _get_dataset_table(
        selected_names or [],
        selected_variants or [],
        selected_types or [],
        selected_sexes or [],
        effective_age,
        bool(include_unknown_age),
        bool(include_unknown_sex),
        bool(include_unknown_variant),
        bool(require_wildtype),
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
# Callbacks 2a-b: age unit / inputs <-> age-range-days store
# ---------------------------------------------------------------------------


@callback(
    Output("age-min-input", "value"),
    Output("age-max-input", "value"),
    Input("age-unit", "value"),
    State("age-range-days", "data"),
    prevent_initial_call=True,
)
def _convert_age_inputs_on_unit_change(unit, age_days):
    """Re-express the stored day range in the newly selected unit."""
    min_days, max_days = age_days if age_days else [_age_min, _age_max]
    return _from_days(int(min_days), unit), _from_days(int(max_days), unit)


@callback(
    Output("age-range-days", "data"),
    Input("age-min-input", "value"),
    Input("age-max-input", "value"),
    State("age-unit", "value"),
    prevent_initial_call=True,
)
def _update_age_days_store(min_val, max_val, unit):
    """Convert the entered min/max to days and persist in the Store."""
    effective_unit = unit or "days"
    lo = _to_days(min_val if min_val is not None else 0, effective_unit)
    hi = _to_days(max_val if max_val is not None else _age_max, effective_unit)
    return [min(lo, hi), max(lo, hi)]


# ---------------------------------------------------------------------------
# Callback 2: search value -> gene options (server-side filtered)
# ---------------------------------------------------------------------------


@callback(
    Output("gene-select", "options"),
    Input("gene-select", "search_value"),
    State("gene-select", "value"),
    State("url", "search"),
)
def filter_gene_options(search, current_gene, url_search):
    """Return matching genes while keeping the selected gene visible.

    The gene supplied in the URL is also included so that a gene selected
    from the landing-page search remains visible in the dropdown when the
    charts page loads.
    """
    genes = _search_genes(search or "")

    url_gene = _resolve_url_gene(url_search)

    genes_to_keep = []
    if current_gene:
        genes_to_keep.append(current_gene)

    if url_gene and url_gene not in genes_to_keep:
        genes_to_keep.append(url_gene)

    genes = genes_to_keep + [gene for gene in genes if gene not in genes_to_keep]

    return [{"label": gene, "value": gene} for gene in genes]


# ---------------------------------------------------------------------------
# Callback 4: dataset -> reset group/sample-type/sex/age selections;
# gene selection is preserved across dataset changes (except on first load,
# where a valid ?gene=<name> URL param takes priority)
# ---------------------------------------------------------------------------


@callback(
    Output("gene-select", "value"),
    Output("group-select", "options"),
    Output("group-select", "value"),
    Output("plot-sample-type-select", "options"),
    Output("plot-sample-type-select", "value"),
    Output("plot-sex-select", "options"),
    Output("plot-sex-select", "value"),
    Output("plot-age-select", "options"),
    Output("plot-age-select", "value"),
    Output("url-gene-applied", "data"),
    Input("dataset-selected", "data"),
    State("gene-select", "value"),
    State("url", "search"),
    State("url-gene-applied", "data"),
)
def update_selectors(bioproject, current_gene, url_search, url_gene_applied):
    """Reset group, sample type, sex, and age selections when the dataset
    changes. The gene selection is handled specially:

    - On the very first load, a valid ?gene=<name> URL param (from the
      landing-page search box) takes priority as the default.
    - On every subsequent dataset change, whatever gene the user currently
      has selected is preserved, rather than resetting to the first
      alphabetical gene or re-applying the original URL param.
    """
    if not bioproject:
        return None, [], [], [], [], [], [], [], [], url_gene_applied

    genes = _search_genes("")
    genotypes = _get_genotypes(bioproject)
    sample_types = _get_sample_types_for_dataset(bioproject)
    sexes = _get_sexes_for_dataset(bioproject)
    age_range_opts = _get_age_ranges_for_dataset(bioproject)

    if not url_gene_applied:
        url_gene = _resolve_url_gene(url_search)
        default_gene = url_gene or current_gene or (genes[0] if genes else None)
        gene_applied = True
    else:
        default_gene = current_gene or (genes[0] if genes else None)
        gene_applied = url_gene_applied

    return (
        default_gene,
        [{"label": g, "value": g} for g in genotypes],
        genotypes,
        [{"label": _readable_sample_type(st), "value": st} for st in sample_types],
        sample_types,
        [{"label": s, "value": s} for s in sexes],
        sexes,
        age_range_opts,
        [opt["value"] for opt in age_range_opts],
        gene_applied,
    )


# ---------------------------------------------------------------------------
# Callback 5: gene + groups + stat test -> render plot
# ---------------------------------------------------------------------------


@callback(
    Output("violin-plot", "figure"),
    Output("download-meta", "children"),
    Input("dataset-selected", "data"),
    Input("gene-select", "value"),
    Input("group-select", "value"),
    Input("plot-sample-type-select", "value"),
    Input("plot-sex-select", "value"),
    Input("plot-age-select", "value"),
    Input("stat-test", "value"),
    State("group-select", "options"),
)
def update_plot(
    bioproject,
    gene,
    selected_groups,
    selected_sample_types,
    selected_sexes,
    selected_age_ranges,
    stat_test,
    all_group_options,
):
    """Query TPM values for the selected gene and render the violin plot."""
    meta = f"{bioproject}_{gene}" if bioproject and gene else ""
    if (
        not bioproject
        or not gene
        or not selected_groups
        or not selected_sample_types
        or not selected_sexes
        or not selected_age_ranges
    ):
        return {}, meta

    df = _get_tpm_data(
        bioproject, gene, selected_sample_types, selected_sexes, selected_age_ranges
    )
    if df.empty:
        return {}, meta

    all_genotypes = sorted(df["genotype"].unique())
    df = df[df["genotype"].isin(selected_groups)]

    # Assign colors by group identity using the full options list so colors
    # stay stable when groups are removed from the filter.
    all_option_values = [opt["value"] for opt in (all_group_options or [])]
    stable_palette = {
        g: DEFAULT_COLORS[i % len(DEFAULT_COLORS)]
        for i, g in enumerate(all_option_values)
    }

    fig = plot_tpm_violin_plotly(
        df,
        group_col="genotype",
        group_label="Group",
        group_order=[g for g in all_genotypes if g in selected_groups],
        stat_test=None if stat_test == "none" else stat_test,
        title=gene,
        palette=stable_palette,
    )

    y_min, y_max = _get_tpm_range(bioproject, gene)
    pad = (y_max - y_min) * 0.05 if y_max > y_min else 0.5
    fig.update_layout(yaxis=dict(range=[y_min - pad, y_max + pad]))

    return fig, meta


# ---------------------------------------------------------------------------
# Callback 6: gene + groups -> populate accessible data table
# ---------------------------------------------------------------------------


@callback(
    Output("table-status", "children"),
    Output("tpm-data-table", "children"),
    Input("dataset-selected", "data"),
    Input("gene-select", "value"),
    Input("group-select", "value"),
    Input("plot-sample-type-select", "value"),
    Input("plot-sex-select", "value"),
    Input("plot-age-select", "value"),
)
def update_table(
    bioproject,
    gene,
    selected_groups,
    selected_sample_types,
    selected_sexes,
    selected_age_ranges,
):
    """Build a per-genotype summary table of log10(TPM+1) statistics.

    No-data states are reported via the sibling #table-status paragraph rather
    than an html.Caption inside the table.  A table that contains only a
    caption (no <th> elements) is misidentified as a layout table by axe-core,
    which then flags the caption as a WCAG violation.
    """
    if (
        not bioproject
        or not gene
        or not selected_groups
        or not selected_sample_types
        or not selected_sexes
        or not selected_age_ranges
    ):
        return "No data to display. Select a dataset, gene, and groups.", []

    df = _get_tpm_data(
        bioproject, gene, selected_sample_types, selected_sexes, selected_age_ranges
    )
    if df.empty:
        return "No expression data found for the current selection.", []

    df = df[df["genotype"].isin(selected_groups)]
    n_samples = len(df)
    n_genotypes = df["genotype"].nunique()

    df["log_tpm"] = df["TPM"].apply(lambda x: math.log10(x + 1))
    summary = (
        df.groupby("genotype")
        .agg(
            n=("log_tpm", "count"),
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
            f"{gene} expression — {n_samples} samples, {n_genotypes} group(s)"
        ),
        html.Thead(
            html.Tr(
                [
                    html.Th("Group (n)", scope="col"),
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
                        html.Td(f"{row['genotype']} ({row['n']})"),
                        html.Td(
                            [
                                html.Span(
                                    f"{row['Max']:.4f}",
                                    **{"aria-hidden": "true"},
                                ),
                                html.Span(
                                    _aria_decimal(row["Max"]),
                                    className="visually-hidden",
                                ),
                            ]
                        ),
                        html.Td(
                            [
                                html.Span(
                                    f"{row['Q3']:.4f}",
                                    **{"aria-hidden": "true"},
                                ),
                                html.Span(
                                    _aria_decimal(row["Q3"]),
                                    className="visually-hidden",
                                ),
                            ]
                        ),
                        html.Td(
                            [
                                html.Span(
                                    f"{row['Median']:.4f}",
                                    **{"aria-hidden": "true"},
                                ),
                                html.Span(
                                    _aria_decimal(row["Median"]),
                                    className="visually-hidden",
                                ),
                            ]
                        ),
                        html.Td(
                            [
                                html.Span(
                                    f"{row['Q1']:.4f}",
                                    **{"aria-hidden": "true"},
                                ),
                                html.Span(
                                    _aria_decimal(row["Q1"]),
                                    className="visually-hidden",
                                ),
                            ]
                        ),
                        html.Td(
                            [
                                html.Span(
                                    f"{row['Min']:.4f}",
                                    **{"aria-hidden": "true"},
                                ),
                                html.Span(
                                    _aria_decimal(row["Min"]),
                                    className="visually-hidden",
                                ),
                            ]
                        ),
                    ]
                )
                for _, row in summary.iterrows()
            ]
        ),
    ]
