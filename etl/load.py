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
from psycopg2.extras import NumericRange, execute_values  # type: ignore[import-untyped]

from db.connection import SessionLocal, engine
from db.models import Dataset, Gene, Sample, SampleGene

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


_TPM_BATCH_SIZE = 10_000
_TPM_INSERT_SQL = (
    "INSERT INTO sample_gene (sample_id, gene_id, tpm)"
    " VALUES %s ON CONFLICT (sample_id, gene_id) DO NOTHING"
)


def load_genes(staging: Path | None = None) -> int:
    """Load gene identifiers from a reference TPM file into the gene table.

    All PRJNA TPM files share the same 78,317-row Ensembl gene annotation, so
    only the first file found is read. Rows already present (by gene_id string)
    are skipped. Returns the count of newly inserted rows.
    """
    if staging is None:
        staging = _staging_dir()

    tpm_dir = staging / "tpm"
    tpm_files = sorted(tpm_dir.glob("*/salmon.merged.gene_tpm.tsv"))
    if not tpm_files:
        raise FileNotFoundError(
            f"No salmon.merged.gene_tpm.tsv files found under {tpm_dir}. "
            "Run etl/download.py first."
        )

    ref_file = tpm_files[0]
    genes: list[tuple[str, str | None]] = []
    with open(ref_file, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            gene_name = row["gene_name"].strip() or None
            genes.append((row["gene_id"].strip(), gene_name))

    session = SessionLocal()
    inserted = 0
    try:
        existing = {gid for (gid,) in session.query(Gene.gene_id).all()}
        new_genes = [
            {"gene_id": gid, "gene_name": gname}
            for gid, gname in genes
            if gid not in existing
        ]
        if new_genes:
            session.bulk_insert_mappings(Gene, new_genes)  # type: ignore[arg-type]
            session.commit()
            inserted = len(new_genes)
        log.info(
            "Loaded %d new gene rows (skipped %d already present).",
            inserted,
            len(genes) - inserted,
        )
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return inserted


def load_tpm(staging: Path | None = None) -> int:
    """Load TPM expression values from salmon.merged.gene_tpm.tsv files.

    Each file has columns gene_id, gene_name, then one column per SRR run ID.
    Sample IDs are resolved via the sample table; gene IDs via the gene table.
    Rows are bulk-inserted via psycopg2 execute_values for performance. Any
    sample that already has rows in sample_gene is skipped. Returns the
    total count of rows inserted across all files.
    """
    if staging is None:
        staging = _staging_dir()

    tpm_dir = staging / "tpm"
    if not tpm_dir.exists():
        raise FileNotFoundError(
            f"TPM directory not found at {tpm_dir}. Run etl/download.py first."
        )

    tpm_files = sorted(tpm_dir.glob("*/salmon.merged.gene_tpm.tsv"))
    if not tpm_files:
        log.warning("No TPM files found under %s.", tpm_dir)
        return 0

    session = SessionLocal()
    try:
        run_to_sid: dict[str, int] = {
            run: sid for run, sid in session.query(Sample.run, Sample.id).all()
        }
        gene_str_to_id: dict[str, int] = {
            gid: dbid for gid, dbid in session.query(Gene.gene_id, Gene.id).all()
        }
        if not gene_str_to_id:
            raise RuntimeError(
                "Gene table is empty. Run load_genes() before load_tpm()."
            )
        loaded_sids: set[int] = {
            sid for (sid,) in session.query(SampleGene.sample_id).distinct().all()
        }
    finally:
        session.close()

    conn = engine.raw_connection()
    total_inserted = 0
    try:
        for tpm_file in tpm_files:
            bioproject = tpm_file.parent.name
            log.info("Loading TPM from %s", bioproject)

            with open(tpm_file, newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh, delimiter="\t")
                run_cols = [
                    c
                    for c in (reader.fieldnames or [])
                    if c not in ("gene_id", "gene_name")
                ]
                col_to_sid: dict[str, int] = {}
                for run in run_cols:
                    sid = run_to_sid.get(run)
                    if sid is None:
                        log.warning(
                            "Run %s (%s) not in sample table; skipping.",
                            run,
                            bioproject,
                        )
                    elif sid in loaded_sids:
                        log.info("Run %s already loaded; skipping.", run)
                    else:
                        col_to_sid[run] = sid

                if not col_to_sid:
                    log.info("No new samples in %s; skipping.", bioproject)
                    continue

                batch: list[tuple[int, int, float]] = []
                cur = conn.cursor()
                try:
                    for row in reader:
                        gene_db_id = gene_str_to_id.get(row["gene_id"])
                        if gene_db_id is None:
                            continue
                        for run, sid in col_to_sid.items():
                            raw = row.get(run) or "0"
                            batch.append((sid, gene_db_id, float(raw)))
                            if len(batch) >= _TPM_BATCH_SIZE:
                                execute_values(cur, _TPM_INSERT_SQL, batch)
                                total_inserted += len(batch)
                                batch = []
                    if batch:
                        execute_values(cur, _TPM_INSERT_SQL, batch)
                        total_inserted += len(batch)
                finally:
                    cur.close()

                conn.commit()
                loaded_sids.update(col_to_sid.values())
                log.info(
                    "Loaded TPM for %d samples from %s.",
                    len(col_to_sid),
                    bioproject,
                )
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    log.info("Loaded %d total TPM rows.", total_inserted)
    return total_inserted


if __name__ == "__main__":
    load_datasets()
    load_samples()
    load_genes()
    load_tpm()
