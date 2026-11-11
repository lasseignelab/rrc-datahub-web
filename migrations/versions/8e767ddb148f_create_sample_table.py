"""create sample table

Revision ID: 8e767ddb148f
Revises: 4df4fc616701
Create Date: 2026-06-26 19:12:44.517547

"""

# pylint: disable=no-member
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "8e767ddb148f"
down_revision: Union[str, Sequence[str], None] = "4df4fc616701"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the sample table."""
    op.create_table(
        "sample",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("dataset_id", sa.Integer(), nullable=False),
        sa.Column("run", sa.String(length=20), nullable=False),
        sa.Column("biosample", sa.String(length=20), nullable=True),
        sa.Column("sample_name", sa.String(length=100), nullable=True),
        sa.Column("experiment", sa.String(length=20), nullable=True),
        sa.Column("sra_study", sa.String(length=20), nullable=True),
        sa.Column("submission", sa.String(length=20), nullable=True),
        sa.Column("release_date", sa.DateTime(), nullable=True),
        sa.Column("load_date", sa.DateTime(), nullable=True),
        sa.Column("bases", sa.BigInteger(), nullable=True),
        sa.Column("spots", sa.BigInteger(), nullable=True),
        sa.Column("avg_length", sa.Integer(), nullable=True),
        sa.Column("size_mb", sa.Integer(), nullable=True),
        sa.Column("library_layout", sa.String(length=10), nullable=True),
        sa.Column("platform", sa.String(length=50), nullable=True),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("fastq_ftp", sa.Text(), nullable=True),
        sa.Column("fastq_md5", sa.String(length=32), nullable=True),
        sa.Column("run_hash", sa.String(length=32), nullable=True),
        sa.Column("read_hash", sa.String(length=32), nullable=True),
        sa.Column("tax_id", sa.Integer(), nullable=True),
        sa.Column("scientific_name", sa.String(length=100), nullable=True),
        sa.Column("source_name", sa.String(length=200), nullable=True),
        sa.Column("sample_type", sa.String(length=50), nullable=True),
        sa.Column("underlying_variant", sa.String(length=200), nullable=True),
        sa.Column("genotype", sa.String(length=200), nullable=True),
        sa.Column("strain", sa.String(length=200), nullable=True),
        sa.Column("strain_raw", sa.String(length=200), nullable=True),
        sa.Column("tissue", sa.String(length=100), nullable=True),
        sa.Column("age_raw", sa.String(length=100), nullable=True),
        sa.Column("age_range", postgresql.NUMRANGE(), nullable=True),
        sa.Column("sex", sa.String(length=20), nullable=True),
        sa.Column("treatment", sa.String(length=200), nullable=True),
        sa.Column("treatment_group", sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(["dataset_id"], ["dataset.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run"),
    )
    op.create_index("ix_sample_dataset_id", "sample", ["dataset_id"])


def downgrade() -> None:
    """Drop the sample table."""
    op.drop_index("ix_sample_dataset_id", table_name="sample")
    op.drop_table("sample")
