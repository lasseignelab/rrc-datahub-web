# SQLAlchemy ORM models for the RRC DataHub database.

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import NUMRANGE
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


class Dataset(Base):
    """One row per GEO BioProject dataset."""

    __tablename__ = "dataset"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bioproject: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)

    def __repr__(self) -> str:
        """Return a developer-readable representation."""
        return f"Dataset(id={self.id!r}, bioproject={self.bioproject!r})"


class Sample(Base):
    """One row per SRA run (sequencing sample) within a BioProject dataset."""

    __tablename__ = "sample"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dataset.id"), nullable=False, index=True
    )
    run: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    biosample: Mapped[str | None] = mapped_column(String(20))
    sample_name: Mapped[str | None] = mapped_column(String(100))
    experiment: Mapped[str | None] = mapped_column(String(20))
    sra_study: Mapped[str | None] = mapped_column(String(20))
    submission: Mapped[str | None] = mapped_column(String(20))
    release_date: Mapped[datetime | None] = mapped_column(DateTime)
    load_date: Mapped[datetime | None] = mapped_column(DateTime)
    bases: Mapped[int | None] = mapped_column(BigInteger)
    spots: Mapped[int | None] = mapped_column(BigInteger)
    avg_length: Mapped[int | None] = mapped_column(Integer)
    size_mb: Mapped[int | None] = mapped_column(Integer)
    library_layout: Mapped[str | None] = mapped_column(String(10))
    platform: Mapped[str | None] = mapped_column(String(50))
    model: Mapped[str | None] = mapped_column(String(100))
    fastq_ftp: Mapped[str | None] = mapped_column(Text)
    fastq_md5: Mapped[str | None] = mapped_column(Text)
    run_hash: Mapped[str | None] = mapped_column(String(32))
    read_hash: Mapped[str | None] = mapped_column(String(32))
    tax_id: Mapped[int | None] = mapped_column(Integer)
    scientific_name: Mapped[str | None] = mapped_column(String(100))
    source_name: Mapped[str | None] = mapped_column(String(200))
    sample_type: Mapped[str | None] = mapped_column(String(50))
    underlying_variant: Mapped[str | None] = mapped_column(String(200))
    genotype: Mapped[str | None] = mapped_column(String(200))
    strain: Mapped[str | None] = mapped_column(String(200))
    strain_raw: Mapped[str | None] = mapped_column(String(200))
    tissue: Mapped[str | None] = mapped_column(String(100))
    age_raw: Mapped[str | None] = mapped_column(String(100))
    age_range: Mapped[Any] = mapped_column(NUMRANGE, nullable=True)
    sex: Mapped[str | None] = mapped_column(String(20))
    treatment: Mapped[str | None] = mapped_column(String(200))
    treatment_group: Mapped[str | None] = mapped_column(String(200))

    def __repr__(self) -> str:
        """Return a developer-readable representation."""
        return (
            f"Sample(id={self.id!r}, run={self.run!r}, dataset_id={self.dataset_id!r})"
        )


class Gene(Base):
    """One row per reference gene from the Ensembl annotation."""

    __tablename__ = "gene"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    gene_id: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    gene_name: Mapped[str | None] = mapped_column(String(100))

    def __repr__(self) -> str:
        """Return a developer-readable representation."""
        return f"Gene(id={self.id!r}, gene_id={self.gene_id!r})"


class SampleGene(Base):
    """Per-sample, per-gene expression values (salmon output)."""

    __tablename__ = "sample_gene"
    __table_args__ = (Index("ix_sample_gene_gene_id", "gene_id"),)

    sample_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sample.id"), primary_key=True
    )
    gene_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("gene.id"), primary_key=True
    )
    tpm: Mapped[float] = mapped_column(Float, nullable=False)

    def __repr__(self) -> str:
        """Return a developer-readable representation."""
        return (
            f"SampleGene(sample_id={self.sample_id!r},"
            f" gene_id={self.gene_id!r}, tpm={self.tpm!r})"
        )
