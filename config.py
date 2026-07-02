from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_DIR   = BASE_DIR / "db"


def get_available_datasets() -> list[str]:
    """Scan db/ for subdirectories (e.g. PRJNA285844)."""
    return sorted([d.name for d in DB_DIR.iterdir() if d.is_dir()])


def dataset_paths(accession: str) -> dict:
    d = DB_DIR / accession
    return {
        "tpm":      d / "salmon.merged.gene_tpm.tsv",
        "samples":  d / "samplesheet.csv",
        "metadata": d / "extended_metadata.csv",
    }
