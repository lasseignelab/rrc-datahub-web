# ETL load step: reads staged files and inserts records into the database.

# pylint: disable=import-error
import csv
import logging
import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from dotenv import load_dotenv  # type: ignore[import-untyped]
from psycopg2.extras import NumericRange  # type: ignore[import-untyped]

from db.connection import SessionLocal
from db.models import Dataset, Sample

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

_NUMERIC_NULLS = {"NP", "NA", ""}


def _staging_dir() -> Path:
    """Return the local staging directory."""
    return Path(os.getenv("STAGING_DIR", "staging"))


def _opt_str(val: str) -> str | None:
    """Return None for blank strings; preserve other values including 'NP' and 'NA'."""
    stripped = val.strip()
    return None if stripped == "" else stripped


def _opt_int(val: str) -> int | None:
    """Parse val as int, returning None for non-numeric sentinel values."""
    stripped = val.strip()
    if stripped in _NUMERIC_NULLS:
        return None
    return int(stripped)


def _opt_datetime(val: str) -> datetime | None:
    """Parse val as a datetime, returning None for sentinel values."""
    stripped = val.strip()
    if stripped in _NUMERIC_NULLS:
        return None
    return datetime.strptime(stripped, "%Y-%m-%d %H:%M:%S")


def _opt_numrange(lower_str: str, upper_str: str) -> Any:
    """Build a closed NumericRange from two strings, or None if either is a sentinel."""
    lower_stripped = lower_str.strip()
    upper_stripped = upper_str.strip()
    if lower_stripped in _NUMERIC_NULLS or upper_stripped in _NUMERIC_NULLS:
        return None
    lower = Decimal(lower_stripped)
    upper = Decimal(upper_stripped)
    return NumericRange(lower, upper, bounds="[]")  # type: ignore[arg-type]


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


def load_samples(staging: Path | None = None) -> int:
    """Load sample metadata from transformed-metadata TSV files into the sample table.

    Scans staging/transformed-metadata/ for *_transformed.tsv files, looks up each
    row's dataset_id by bioproject, and inserts rows not already present (by run).
    Returns the total count of newly inserted rows.
    """
    if staging is None:
        staging = _staging_dir()

    metadata_dir = staging / "transformed-metadata"
    if not metadata_dir.exists():
        raise FileNotFoundError(
            f"transformed-metadata directory not found at {metadata_dir}. "
            "Run etl/download.py first."
        )

    tsv_files = sorted(metadata_dir.glob("**/*_transformed.tsv"))
    if not tsv_files:
        log.warning("No *_transformed.tsv files found under %s.", metadata_dir)
        return 0

    session = SessionLocal()
    inserted = 0
    skipped = 0
    try:
        bioproject_to_id = {
            bp: did for bp, did in session.query(Dataset.bioproject, Dataset.id).all()
        }
        existing_runs = {run for (run,) in session.query(Sample.run).all()}

        for tsv_path in tsv_files:
            log.info("Loading %s", tsv_path)
            with open(tsv_path, newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh, delimiter="\t")
                for row in reader:
                    run = row["run"].strip()
                    if run in existing_runs:
                        skipped += 1
                        continue

                    bioproject = row["bioproject"].strip()
                    dataset_id = bioproject_to_id.get(bioproject)
                    if dataset_id is None:
                        log.warning(
                            "Skipping run %s — bioproject %s not in dataset table.",
                            run,
                            bioproject,
                        )
                        skipped += 1
                        continue

                    session.add(
                        Sample(
                            dataset_id=dataset_id,
                            run=run,
                            biosample=_opt_str(row["biosample"]),
                            sample_name=_opt_str(row["sample_name"]),
                            experiment=_opt_str(row["experiment"]),
                            sra_study=_opt_str(row["sra_study"]),
                            submission=_opt_str(row["submission"]),
                            release_date=_opt_datetime(row["release_date"]),
                            load_date=_opt_datetime(row["load_date"]),
                            bases=_opt_int(row["bases"]),
                            spots=_opt_int(row["spots"]),
                            avg_length=_opt_int(row["avg_length"]),
                            size_mb=_opt_int(row["size_mb"]),
                            library_layout=_opt_str(row["library_layout"]),
                            platform=_opt_str(row["platform"]),
                            model=_opt_str(row["model"]),
                            fastq_ftp=_opt_str(row["fastq_ftp"]),
                            fastq_md5=_opt_str(row["fastq_md5"]),
                            run_hash=_opt_str(row["run_hash"]),
                            read_hash=_opt_str(row["read_hash"]),
                            tax_id=_opt_int(row["tax_id"]),
                            scientific_name=_opt_str(row["scientific_name"]),
                            source_name=_opt_str(row["source_name"]),
                            sample_type=_opt_str(row["sample_type"]),
                            underlying_variant=_opt_str(row["underlying_variant"]),
                            genotype=_opt_str(row["genotype"]),
                            strain=_opt_str(row["strain"]),
                            strain_raw=_opt_str(row["strain_raw"]),
                            tissue=_opt_str(row["tissue"]),
                            age_raw=_opt_str(row["age_raw"]),
                            age_range=_opt_numrange(
                                row["age_range_lower"], row["age_range_upper"]
                            ),
                            sex=_opt_str(row["sex"]),
                            treatment=_opt_str(row["treatment"]),
                            treatment_group=_opt_str(row["treatment_group"]),
                        )
                    )
                    existing_runs.add(run)
                    inserted += 1

        session.commit()
        log.info(
            "Loaded %d sample rows; skipped %d (already present or no dataset match).",
            inserted,
            skipped,
        )
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return inserted


if __name__ == "__main__":
    load_datasets()
    load_samples()
