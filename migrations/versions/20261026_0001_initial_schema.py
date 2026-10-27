"""Create the initial application schema.

Revision ID: 20261026_0001
Revises:
Create Date: 2026-10-26
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20261026_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    tables = set(inspector.get_table_names())

    if "users" not in tables:
        op.create_table(
            "users",
            sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
            sa.Column("email", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("hashed_password", sa.String(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("email"),
        )
        op.create_index("ix_users_email", "users", ["email"], unique=False)
    elif "hashed_password" not in {
        column["name"] for column in inspector.get_columns("users")
    }:
        op.add_column(
            "users",
            sa.Column(
                "hashed_password",
                sa.String(),
                nullable=False,
                server_default="",
            ),
        )

    if "workouts" not in tables:
        op.create_table(
            "workouts",
            sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("description", sa.String(), nullable=True),
            sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_workouts_user_id", "workouts", ["user_id"], unique=False)


def downgrade() -> None:
    inspector = inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if "workouts" in tables:
        op.drop_index("ix_workouts_user_id", table_name="workouts")
        op.drop_table("workouts")
    if "users" in tables:
        op.drop_index("ix_users_email", table_name="users")
        op.drop_table("users")
