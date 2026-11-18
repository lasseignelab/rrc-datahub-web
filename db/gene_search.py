"""
Validates a typed gene name against the real gene list, with a small
tolerance for casing/typos -- same approach as validate.py from the
NL-query prototype, pulled out here since this feature doesn't need
the rest of that module (no LLM extraction step at all).
"""

from dataclasses import dataclass
from difflib import get_close_matches
from functools import lru_cache

from db.connection import SessionLocal
from db.models import Gene, Sample, SampleGene


@dataclass
class GeneSearchResult:
    query: str
    resolved_gene: str | None
    scientific_name: str | None
    corrected: bool
    error: str | None = None


@lru_cache(maxsize=1)
def get_valid_genes() -> set[str]:
    """Return the set of known gene names, queried once and cached.

    Cache is fine since the gene reference table changes rarely relative
    to how often searches come in. If genes get added/updated during a
    running session, call get_valid_genes.cache_clear() to refresh.
    """
    session = SessionLocal()
    try:
        rows = session.query(Gene.gene_name).filter(Gene.gene_name.isnot(None)).all()
        return {r[0] for r in rows}
    finally:
        session.close()


def _get_gene_scientific_name(gene_name: str) -> str | None:
    """Return the scientific name associated with a gene.

    Returns None if the gene has no associated species.
    """
    session = SessionLocal()
    try:
        species = (
            session.query(Sample.scientific_name)
            .join(SampleGene, SampleGene.sample_id == Sample.id)
            .join(Gene, Gene.id == SampleGene.gene_id)
            .filter(
                Gene.gene_name == gene_name,
                Sample.scientific_name.isnot(None),
            )
            .distinct()
            .all()
        )

        if len(species) == 1:
            return species[0][0]

        return None

    finally:
        session.close()


def resolve_gene(query: str) -> GeneSearchResult:
    query = query.strip()

    if not query:
        return GeneSearchResult(
            query=query,
            resolved_gene=None,
            scientific_name=None,
            corrected=False,
            error="Enter a gene name to search.",
        )

    valid_genes = get_valid_genes()

    resolved_gene = None
    corrected = False

    # 1. Prioritize an exact, case-sensitive match.
    if query in valid_genes:
        resolved_gene = query

    else:
        # 2. Find case-insensitive matches.
        case_matches = [
            gene for gene in valid_genes
            if gene.lower() == query.lower()
        ]

        if len(case_matches) == 1:
            resolved_gene = case_matches[0]

        elif len(case_matches) > 1:
            return GeneSearchResult(
                query=query,
                resolved_gene=None,
                scientific_name=None,
                corrected=False,
                error=(
                    f"Multiple genes match '{query}' with different "
                    "capitalization. Please enter the gene name "
                    "using its correct capitalization."
                ),
            )

        else:
            # 3. Try fuzzy matching, excluding ambiguous case variants.
            lowercase_counts = {}
            for gene in valid_genes:
                key = gene.lower()
                lowercase_counts[key] = lowercase_counts.get(key, 0) + 1

            unambiguous_genes = [
                gene for gene in valid_genes
                if lowercase_counts[gene.lower()] == 1
            ]

            close = get_close_matches(
                query,
                unambiguous_genes,
                n=1,
                cutoff=0.8,
            )

            if close:
                resolved_gene = close[0]
                corrected = True

    if not resolved_gene:
        return GeneSearchResult(
            query=query,
            resolved_gene=None,
            scientific_name=None,
            corrected=False,
            error=f"No gene matching '{query}' found in DataHub.",
        )

    scientific_name = _get_gene_scientific_name(resolved_gene)

    if not scientific_name:
        return GeneSearchResult(
            query=query,
            resolved_gene=None,
            scientific_name=None,
            corrected=corrected,
            error=(
                f"Could not determine a unique scientific species "
                f"for gene '{resolved_gene}'."
            ),
        )

    return GeneSearchResult(
        query=query,
        resolved_gene=resolved_gene,
        scientific_name=scientific_name,
        corrected=corrected,
    )