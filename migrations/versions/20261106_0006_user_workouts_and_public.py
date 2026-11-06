"""Add user-workout memberships and public visibility.

Revision ID: 20261106_0006
Revises: 20261106_0005
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20261106_0006"
down_revision: Union[str, None] = "20261106_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "workouts",
        sa.Column("public", sa.Boolean(), nullable=True),
    )
    op.execute(sa.text("UPDATE workouts SET public = false"))
    op.alter_column("workouts", "public", nullable=False)

    op.create_table(
        "user_workouts",
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("workout_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("owner", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workout_id"], ["workouts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "workout_id"),
    )
    op.execute(
        sa.text(
            "INSERT INTO user_workouts (user_id, workout_id, owner) "
            "SELECT user_id, id, true FROM workouts"
        )
    )

    op.drop_constraint("workouts_user_id_fkey", "workouts", type_="foreignkey")
    op.drop_index("ix_workouts_user_id", table_name="workouts")
    op.drop_column("workouts", "user_id")


def downgrade() -> None:
    bind = op.get_bind()
    op.add_column(
        "workouts",
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=True),
    )

    owner_rows = bind.execute(
        sa.text("SELECT workout_id, user_id FROM user_workouts WHERE owner = true")
    ).all()
    owner_workout_ids = {workout_id for workout_id, _ in owner_rows}
    workout_ids = set(bind.execute(sa.text("SELECT id FROM workouts")).scalars())
    if owner_workout_ids != workout_ids:
        raise RuntimeError("Cannot downgrade: every workout must have an owner")

    for workout_id, user_id in owner_rows:
        bind.execute(
            sa.text("UPDATE workouts SET user_id = :user_id WHERE id = :workout_id"),
            {"user_id": user_id, "workout_id": workout_id},
        )

    op.alter_column("workouts", "user_id", nullable=False)
    op.create_foreign_key(
        "workouts_user_id_fkey", "workouts", "users", ["user_id"], ["id"]
    )
    op.create_index("ix_workouts_user_id", "workouts", ["user_id"], unique=False)
    op.drop_table("user_workouts")
    op.drop_column("workouts", "public")