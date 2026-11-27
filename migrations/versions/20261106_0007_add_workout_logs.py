"""Add persistent workout logs.

Revision ID: 20261106_0007
Revises: 20261106_0006
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20261106_0007"
down_revision: Union[str, None] = "20261106_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "workout_logs",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "workout_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("workouts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("performed_on", sa.Date(), nullable=False),
    )
    op.create_index("ix_workout_logs_user_id", "workout_logs", ["user_id"])
    op.create_index("ix_workout_logs_workout_id", "workout_logs", ["workout_id"])

    op.create_table(
        "workout_log_exercises",
        sa.Column(
            "workout_log_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("workout_logs.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "exercise_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("exercises.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("sets", sa.Integer(), nullable=False),
        sa.Column("reps", sa.Integer(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("exhaustion_level", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("workout_log_exercises")
    op.drop_index("ix_workout_logs_workout_id", table_name="workout_logs")
    op.drop_index("ix_workout_logs_user_id", table_name="workout_logs")
    op.drop_table("workout_logs")
