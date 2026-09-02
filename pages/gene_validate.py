"""
Validates a typed gene name against the real gene list, with a small
tolerance for casing/typos -- same approach as validate.py from the
NL-query prototype, pulled out here since this feature doesn't need
the rest of that module (no LLM extraction step at all).
"""
from dataclasses import dataclass
from difflib import get_close_matches
from functools import lru_cache

from sqlalchemy import select

from db.models import Gene
from db.session import SessionLocal


@dataclass
class GeneSearchResult:
    query: str
    resolved_gene: str | None
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
        rows = session.execute(
            select(Gene.gene_name).where(Gene.gene_name.isnot(None))
        ).scalars().all()
        return set(rows)
    finally:
        session.close()


def resolve_gene(query: str) -> GeneSearchResult:
    query = query.strip()
    if not query:
        return GeneSearchResult(query=query, resolved_gene=None, corrected=False,
                                 error="Enter a gene name to search.")

    valid_genes = get_valid_genes()
    lookup = {g.lower(): g for g in valid_genes}

    if query.lower() in lookup:
        return GeneSearchResult(query=query, resolved_gene=lookup[query.lower()], corrected=False)

    close = get_close_matches(query, valid_genes, n=1, cutoff=0.8)
    if close:
        return GeneSearchResult(query=query, resolved_gene=close[0], corrected=True)

    return GeneSearchResult(
        query=query,
        resolved_gene=None,
        corrected=False,
        error=f"No gene matching '{query}' found in DataHub.",
    )
