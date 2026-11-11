"""create sample_gene table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-09 00:00:00.000000

"""

# pylint: disable=no-member
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the sample_gene table."""
    op.create_table(
        "sample_gene",
        sa.Column("sample_id", sa.Integer(), nullable=False),
        sa.Column("gene_id", sa.Integer(), nullable=False),
        sa.Column("tpm", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["gene_id"], ["gene.id"]),
        sa.ForeignKeyConstraint(["sample_id"], ["sample.id"]),
        sa.PrimaryKeyConstraint("sample_id", "gene_id"),
    )
    op.create_index("ix_sample_gene_gene_id", "sample_gene", ["gene_id"])


def downgrade() -> None:
    """Drop the sample_gene table."""
    op.drop_index("ix_sample_gene_gene_id", table_name="sample_gene")
    op.drop_table("sample_gene")
