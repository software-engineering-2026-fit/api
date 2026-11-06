"""Add an administrator flag to users.

Revision ID: 20261106_0010
Revises: 20261106_0009
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20261106_0010"
down_revision: Union[str, None] = "20261106_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("users", "is_admin")