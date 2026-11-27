"""Convert user and workout identifiers to UUIDs.

Revision ID: 20261026_0002
Revises: 20261026_0001
"""

from typing import Sequence, Union
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision: str = "20261026_0002"
down_revision: Union[str, None] = "20261026_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_uuid_column(column: dict[str, object]) -> bool:
    column_type = column["type"]
    return isinstance(column_type, sa.Uuid) or (
        isinstance(column_type, sa.CHAR) and column_type.length == 32
    )


def _upgrade_sqlite_legacy_ids(bind: sa.Connection) -> None:
    user_rows = bind.execute(sa.text("SELECT id, email, name, hashed_password FROM users")).all()
    user_mapping = {row.id: uuid4() for row in user_rows}
    workout_rows = bind.execute(
        sa.text("SELECT id, name, description, user_id FROM workouts")
    ).all()

    op.create_table(
        "_users_uuid",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "_workouts_uuid",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["_users_uuid.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    users = sa.table(
        "_users_uuid",
        sa.column("id", sa.Uuid(as_uuid=True)),
        sa.column("email", sa.String()),
        sa.column("name", sa.String()),
        sa.column("hashed_password", sa.String()),
    )
    workouts = sa.table(
        "_workouts_uuid",
        sa.column("id", sa.Uuid(as_uuid=True)),
        sa.column("name", sa.String()),
        sa.column("description", sa.String()),
        sa.column("user_id", sa.Uuid(as_uuid=True)),
    )
    if user_rows:
        bind.execute(
            users.insert(),
            [
                {
                    "id": user_mapping[row.id],
                    "email": row.email,
                    "name": row.name,
                    "hashed_password": row.hashed_password,
                }
                for row in user_rows
            ],
        )
    if workout_rows:
        bind.execute(
            workouts.insert(),
            [
                {
                    "id": uuid4(),
                    "name": row.name,
                    "description": row.description,
                    "user_id": user_mapping[row.user_id],
                }
                for row in workout_rows
            ],
        )

    op.drop_table("workouts")
    op.drop_table("users")
    op.rename_table("_users_uuid", "users")
    op.rename_table("_workouts_uuid", "workouts")
    op.create_index("ix_users_email", "users", ["email"], unique=False)
    op.create_index("ix_workouts_user_id", "workouts", ["user_id"], unique=False)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    user_columns = inspector.get_columns("users")
    workout_columns = inspector.get_columns("workouts")
    if any(column["name"] == "id_uuid" for column in user_columns):
        return
    workout_id_columns = {
        column["name"]: column
        for column in workout_columns
        if column["name"] in {"id", "user_id"}
    }
    if (
        _is_uuid_column(next(column for column in user_columns if column["name"] == "id"))
        and _is_uuid_column(workout_id_columns["id"])
        and _is_uuid_column(workout_id_columns["user_id"])
    ):
        return
    if bind.dialect.name == "sqlite":
        _upgrade_sqlite_legacy_ids(bind)
        return

    uuid_type = sa.Uuid(as_uuid=True)
    op.add_column("users", sa.Column("id_uuid", uuid_type, nullable=True))
    op.add_column("workouts", sa.Column("id_uuid", uuid_type, nullable=True))
    op.add_column("workouts", sa.Column("user_id_uuid", uuid_type, nullable=True))

    user_ids = bind.execute(sa.text("SELECT id FROM users")).scalars().all()
    user_mapping = {user_id: uuid4() for user_id in user_ids}
    for old_id, new_id in user_mapping.items():
        bind.execute(
            sa.text("UPDATE users SET id_uuid = :new_id WHERE id = :old_id"),
            {"new_id": new_id, "old_id": old_id},
        )

    workout_rows = bind.execute(
        sa.text("SELECT id, user_id FROM workouts")
    ).all()
    for old_id, old_user_id in workout_rows:
        bind.execute(
            sa.text(
                "UPDATE workouts "
                "SET id_uuid = :new_id, user_id_uuid = :new_user_id "
                "WHERE id = :old_id"
            ),
            {
                "new_id": uuid4(),
                "new_user_id": user_mapping[old_user_id],
                "old_id": old_id,
            },
        )

    op.execute(
        "ALTER TABLE workouts DROP CONSTRAINT IF EXISTS workouts_user_id_fkey"
    )
    op.execute("ALTER TABLE workouts DROP CONSTRAINT workouts_pkey")
    op.execute("ALTER TABLE users DROP CONSTRAINT users_pkey")
    op.drop_index("ix_workouts_user_id", table_name="workouts")
    op.drop_column("workouts", "user_id")
    op.drop_column("workouts", "id")
    op.drop_column("users", "id")
    op.alter_column("users", "id_uuid", new_column_name="id", nullable=False)
    op.alter_column("workouts", "id_uuid", new_column_name="id", nullable=False)
    op.alter_column(
        "workouts", "user_id_uuid", new_column_name="user_id", nullable=False
    )
    op.create_primary_key("users_pkey", "users", ["id"])
    op.create_primary_key("workouts_pkey", "workouts", ["id"])
    op.create_foreign_key(
        "workouts_user_id_fkey", "workouts", "users", ["user_id"], ["id"]
    )
    op.create_index("ix_workouts_user_id", "workouts", ["user_id"], unique=False)


def downgrade() -> None:
    raise NotImplementedError("UUID identifier conversion cannot be safely downgraded")
