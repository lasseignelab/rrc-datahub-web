# ETL load step: reads staged files and inserts records into the database.

import csv
import logging
import os
from pathlib import Path

from db.connection import SessionLocal
from db.models import Dataset
from dotenv import load_dotenv  # type: ignore[import-untyped]

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _staging_dir() -> Path:
    """Return the local staging directory."""
    return Path(os.getenv("STAGING_DIR", "staging"))


def load_datasets(staging: Path | None = None) -> int:
    """Load bioproject accessions from geo_datasets.csv into the dataset table.

    Rows already present (by bioproject) are skipped so the function is safe
    to run more than once.  Returns the count of newly inserted rows.
    """
    if staging is None:
        staging = _staging_dir()

    csv_path = staging / "geo_datasets.csv"
    if not csv_path.exists():
        raise FileNotFoundError(
            f"geo_datasets.csv not found at {csv_path}. Run etl/download.py first."
        )

    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        bioprojects = [row[0].strip() for row in reader if row and row[0].strip()]

    session = SessionLocal()
    inserted = 0
    try:
        existing = {bp for (bp,) in session.query(Dataset.bioproject).all()}
        for bioproject in bioprojects:
            if bioproject not in existing:
                session.add(Dataset(bioproject=bioproject))
                inserted += 1
        session.commit()
        log.info(
            "Loaded %d new dataset rows (skipped %d already present).",
            inserted,
            len(bioprojects) - inserted,
        )
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return inserted


if __name__ == "__main__":
    load_datasets()
