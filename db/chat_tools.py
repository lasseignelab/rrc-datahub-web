"""
Read-only database queries used as tools by the home-page data chat.

Each function returns plain JSON-serializable data so the chat assistant can
hand the result straight to Claude. Column names that callers may filter or
group by are whitelisted in SAMPLE_FIELDS; nothing here builds SQL from free
text, and nothing writes to the database.
"""

from collections.abc import Mapping
from typing import Any

from sqlalchemy import and_, func

from db.connection import SessionLocal
from db.gene_search import resolve_gene
from db.models import Dataset, Gene, Sample, SampleGene

# Sample metadata columns exposed to the assistant, keyed by the name the
# model uses. Keeping this explicit stops the model from reaching columns
# like fastq_ftp or run hashes that mean nothing to a researcher.
SAMPLE_FIELDS: dict[str, Any] = {
    "scientific_name": Sample.scientific_name,
    "sample_type": Sample.sample_type,
    "sex": Sample.sex,
    "underlying_variant": Sample.underlying_variant,
    "genotype": Sample.genotype,
    "strain": Sample.strain,
    "tissue": Sample.tissue,
    "source_name": Sample.source_name,
    "age": Sample.age_raw,
    "treatment": Sample.treatment,
    "treatment_group": Sample.treatment_group,
    "library_layout": Sample.library_layout,
    "platform": Sample.platform,
}

# Row cap on any single tool result, so one broad question cannot flood the
# model's context with thousands of rows.
MAX_ROWS = 200


def _field(name: str):
    """Return the Sample column for a whitelisted field name, or raise."""
    if name not in SAMPLE_FIELDS:
        allowed = ", ".join(sorted(SAMPLE_FIELDS))
        raise ValueError(f"Unknown field '{name}'. Allowed fields: {allowed}.")
    return SAMPLE_FIELDS[name]


def _filter_conditions(filters: Mapping[str, str | None] | None) -> list:
    """Build case-insensitive equality conditions from a field->value map."""
    conditions = []
    for name, value in (filters or {}).items():
        if value is None or value == "":
            continue
        conditions.append(func.lower(_field(name)) == str(value).lower())
    return conditions


def _age_conditions(min_age_days: float | None, max_age_days: float | None) -> list:
    """Return conditions keeping samples whose age range overlaps the bounds."""
    conditions = []
    if min_age_days is not None:
        conditions.append(func.upper(Sample.age_range) >= min_age_days)
    if max_age_days is not None:
        conditions.append(func.lower(Sample.age_range) <= max_age_days)
    return conditions


def list_field_values(field: str) -> dict:
    """Return the distinct values of one sample field with sample counts."""
    column = _field(field)
    session = SessionLocal()
    try:
        rows = (
            session.query(column, func.count(Sample.id))
            .group_by(column)
            .order_by(func.count(Sample.id).desc())
            .limit(MAX_ROWS)
            .all()
        )
        return {
            "field": field,
            "values": [
                {"value": value if value is not None else "(blank)", "samples": n}
                for value, n in rows
            ],
        }
    finally:
        session.close()


def find_datasets(
    filters: dict[str, str] | None = None,
    min_age_days: float | None = None,
    max_age_days: float | None = None,
) -> dict:
    """Return datasets with at least one sample matching every filter."""
    conditions = _filter_conditions(filters) + _age_conditions(
        min_age_days, max_age_days
    )
    session = SessionLocal()
    try:
        query = session.query(Dataset.bioproject, func.count(Sample.id)).join(
            Sample, Sample.dataset_id == Dataset.id
        )
        if conditions:
            query = query.filter(and_(*conditions))
        rows = (
            query.group_by(Dataset.bioproject)
            .order_by(Dataset.bioproject)
            .limit(MAX_ROWS)
            .all()
        )
        return {
            "dataset_count": len(rows),
            "datasets": [
                {"bioproject": bioproject, "matching_samples": n}
                for bioproject, n in rows
            ],
        }
    finally:
        session.close()


def describe_dataset(bioproject: str) -> dict:
    """Return a dataset's sample count and per-field value breakdowns."""
    session = SessionLocal()
    try:
        dataset = (
            session.query(Dataset)
            .filter(func.upper(Dataset.bioproject) == bioproject.strip().upper())
            .first()
        )
        if dataset is None:
            return {"error": f"No dataset with BioProject '{bioproject}'."}

        total = (
            session.query(func.count(Sample.id))
            .filter(Sample.dataset_id == dataset.id)
            .scalar()
        )
        breakdowns = {}
        for name, column in SAMPLE_FIELDS.items():
            rows = (
                session.query(column, func.count(Sample.id))
                .filter(Sample.dataset_id == dataset.id)
                .group_by(column)
                .order_by(func.count(Sample.id).desc())
                .all()
            )
            breakdowns[name] = {
                (value if value is not None else "(blank)"): n for value, n in rows
            }
        return {
            "bioproject": dataset.bioproject,
            "total_samples": total,
            "breakdowns": breakdowns,
        }
    finally:
        session.close()


def gene_expression_summary(
    gene: str,
    group_by: str = "genotype",
    bioproject: str | None = None,
    filters: dict[str, str] | None = None,
) -> dict:
    """Summarize a gene's TPM per dataset and group (n, mean, median, range)."""
    resolved = resolve_gene(gene)
    if resolved.error or not resolved.resolved_gene:
        return {"error": resolved.error or f"Gene '{gene}' not found."}
    gene_name = resolved.resolved_gene
    group_column = _field(group_by)

    conditions = [Gene.gene_name == gene_name] + _filter_conditions(filters)
    if bioproject:
        conditions.append(func.upper(Dataset.bioproject) == bioproject.strip().upper())

    session = SessionLocal()
    try:
        rows = (
            session.query(
                Dataset.bioproject,
                group_column,
                func.count(SampleGene.tpm),
                func.avg(SampleGene.tpm),
                func.percentile_cont(0.5).within_group(SampleGene.tpm),
                func.min(SampleGene.tpm),
                func.max(SampleGene.tpm),
            )
            .join(Gene, Gene.id == SampleGene.gene_id)
            .join(Sample, Sample.id == SampleGene.sample_id)
            .join(Dataset, Dataset.id == Sample.dataset_id)
            .filter(and_(*conditions))
            .group_by(Dataset.bioproject, group_column)
            .order_by(Dataset.bioproject, group_column)
            .limit(MAX_ROWS)
            .all()
        )
        return {
            "gene": gene_name,
            "matched_from": resolved.query if resolved.corrected else None,
            "group_by": group_by,
            "unit": "TPM",
            "groups": [
                {
                    "bioproject": bioproject_name,
                    group_by: group if group is not None else "(blank)",
                    "samples": n,
                    "mean_tpm": round(float(mean), 3),
                    "median_tpm": round(float(median), 3),
                    "min_tpm": round(float(low), 3),
                    "max_tpm": round(float(high), 3),
                }
                for bioproject_name, group, n, mean, median, low, high in rows
            ],
        }
    finally:
        session.close()
