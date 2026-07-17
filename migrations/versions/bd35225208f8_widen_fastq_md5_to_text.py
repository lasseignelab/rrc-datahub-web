"""widen fastq_md5 to text

Revision ID: bd35225208f8
Revises: 8e767ddb148f
Create Date: 2026-06-26 20:02:49.828661

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "bd35225208f8"
down_revision: Union[str, Sequence[str], None] = "8e767ddb148f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(  # pylint: disable=no-member
        "sample",
        "fastq_md5",
        existing_type=sa.VARCHAR(length=32),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(  # pylint: disable=no-member
        "sample",
        "fastq_md5",
        existing_type=sa.Text(),
        type_=sa.VARCHAR(length=32),
        existing_nullable=True,
    )
