"""Add workout logging fields.

Revision ID: 20261106_0005
Revises: 20261106_0004
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20261106_0005"
down_revision: Union[str, None] = "20261106_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "workout_exercises",
        sa.Column("weight_kg", sa.Float(), nullable=True),
    )
    op.add_column(
        "workout_exercises",
        sa.Column("exhaustion_level", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("workout_exercises", "exhaustion_level")
    op.drop_column("workout_exercises", "weight_kg")
