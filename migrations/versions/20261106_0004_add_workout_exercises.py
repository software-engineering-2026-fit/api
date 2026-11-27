"""Add workout_exercises link table.

Revision ID: 20261106_0004
Revises: 20261106_0003
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20261106_0004"
down_revision: Union[str, None] = "20261106_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "workout_exercises",
        sa.Column(
            "workout_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("workouts.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "exercise_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("exercises.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("sets", sa.Integer(), nullable=True),
        sa.Column("reps", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("workout_exercises")
