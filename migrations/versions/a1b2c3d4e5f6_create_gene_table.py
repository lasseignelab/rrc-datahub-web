"""create gene table

Revision ID: a1b2c3d4e5f6
Revises: bd35225208f8
Create Date: 2026-07-09 00:00:00.000000

"""

# pylint: disable=no-member
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "bd35225208f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the gene table."""
    op.create_table(
        "gene",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("gene_id", sa.String(length=30), nullable=False),
        sa.Column("gene_name", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("gene_id"),
    )


def downgrade() -> None:
    """Drop the gene table."""
    op.drop_table("gene")
