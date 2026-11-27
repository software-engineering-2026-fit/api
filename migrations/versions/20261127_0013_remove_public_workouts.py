"""Remove public workout visibility.

Revision ID: 20261127_0013
Revises: 20261113_0012
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20261127_0013"
down_revision: Union[str, None] = "20261113_0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("workouts", "public")


def downgrade() -> None:
    op.add_column(
        "workouts",
        sa.Column("public", sa.Boolean(), nullable=True),
    )
    op.execute(sa.text("UPDATE workouts SET public = false"))
    with op.batch_alter_table(
        "workouts",
        naming_convention={"fk": "%(table_name)s_%(column_0_name)s_fkey"},
    ) as batch_op:
        batch_op.alter_column(
            "public",
            existing_type=sa.Boolean(),
            nullable=False,
        )
