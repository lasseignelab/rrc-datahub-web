"""create dataset table

Revision ID: 4df4fc616701
Revises:
Create Date: 2026-06-25 14:53:40.913052

"""

# pylint: disable=no-member
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4df4fc616701"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the dataset table."""
    op.create_table(
        "dataset",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("bioproject", sa.String(length=20), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bioproject"),
    )


def downgrade() -> None:
    """Drop the dataset table."""
    op.drop_table("dataset")
