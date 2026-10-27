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


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    user_columns = {column["name"] for column in inspector.get_columns("users")}
    if "id_uuid" in user_columns:
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
