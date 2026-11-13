"""Move workout history to UUID-backed memberships, sessions, and set logs.

Revision ID: 20261113_0011
Revises: 20261106_0010
"""

from datetime import date, datetime, time, timezone
from typing import Sequence, Union
from uuid import UUID, uuid4

import sqlalchemy as sa
from alembic import op

revision: str = "20261113_0011"
down_revision: Union[str, None] = "20261106_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _uuid(value: UUID | str) -> UUID:
    return value if isinstance(value, UUID) else UUID(str(value))


def _legacy_exercise_description(row: sa.Row) -> str | None:
    values = []
    if row.sets is not None:
        values.append(f"{row.sets} sets")
    if row.reps is not None:
        values.append(f"{row.reps} reps")
    if row.weight_kg is not None:
        values.append(f"{row.weight_kg:g} kg")
    if row.exhaustion_level is not None:
        values.append(f"exhaustion level {row.exhaustion_level}")
    if not values:
        return None
    return "Legacy planned values: " + ", ".join(values)


def upgrade() -> None:
    bind = op.get_bind()
    user_indexes = {
        index["name"] for index in sa.inspect(bind).get_indexes("users")
    }
    if "ix_users_email" in user_indexes:
        op.drop_index("ix_users_email", table_name="users")
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    old_memberships = sa.table(
        "user_workouts",
        sa.column("user_id", sa.Uuid(as_uuid=True)),
        sa.column("workout_id", sa.Uuid(as_uuid=True)),
        sa.column("owner", sa.Boolean()),
    )
    membership_rows = bind.execute(
        sa.select(
            old_memberships.c.user_id,
            old_memberships.c.workout_id,
            old_memberships.c.owner,
        )
    ).all()

    op.create_table(
        "_user_workouts_new",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("workout_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("owner", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workout_id"], ["workouts.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "user_id", "workout_id", name="uq_user_workouts_user_workout"
        ),
    )
    memberships = sa.table(
        "_user_workouts_new",
        sa.column("id", sa.Uuid(as_uuid=True)),
        sa.column("user_id", sa.Uuid(as_uuid=True)),
        sa.column("workout_id", sa.Uuid(as_uuid=True)),
        sa.column("owner", sa.Boolean()),
    )
    membership_ids: dict[tuple[UUID, UUID], UUID] = {}
    copied_memberships = []
    for row in membership_rows:
        pair = (_uuid(row.user_id), _uuid(row.workout_id))
        membership_id = uuid4()
        membership_ids[pair] = membership_id
        copied_memberships.append(
            {
                "id": membership_id,
                "user_id": pair[0],
                "workout_id": pair[1],
                "owner": row.owner,
            }
        )
    if copied_memberships:
        bind.execute(memberships.insert(), copied_memberships)
    op.drop_table("user_workouts")
    op.rename_table("_user_workouts_new", "user_workouts")
    memberships = sa.table(
        "user_workouts",
        sa.column("id", sa.Uuid(as_uuid=True)),
        sa.column("user_id", sa.Uuid(as_uuid=True)),
        sa.column("workout_id", sa.Uuid(as_uuid=True)),
        sa.column("owner", sa.Boolean()),
    )
    op.create_index("ix_user_workouts_user_id", "user_workouts", ["user_id"])
    op.create_index("ix_user_workouts_workout_id", "user_workouts", ["workout_id"])

    old_workout_exercises = sa.table(
        "workout_exercises",
        sa.column("workout_id", sa.Uuid(as_uuid=True)),
        sa.column("exercise_id", sa.Uuid(as_uuid=True)),
        sa.column("sets", sa.Integer()),
        sa.column("reps", sa.Integer()),
        sa.column("weight_kg", sa.Float()),
        sa.column("exhaustion_level", sa.Integer()),
    )
    old_exercises = bind.execute(
        sa.select(
            old_workout_exercises.c.workout_id,
            old_workout_exercises.c.exercise_id,
            old_workout_exercises.c.sets,
            old_workout_exercises.c.reps,
            old_workout_exercises.c.weight_kg,
            old_workout_exercises.c.exhaustion_level,
        )
    ).all()
    op.create_table(
        "_workout_exercises_new",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("workout_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("exercise_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["workout_id"], ["workouts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercises.id"]),
        sa.UniqueConstraint(
            "workout_id",
            "exercise_id",
            name="uq_workout_exercises_workout_exercise",
        ),
    )
    workout_exercises = sa.table(
        "_workout_exercises_new",
        sa.column("id", sa.Uuid(as_uuid=True)),
        sa.column("workout_id", sa.Uuid(as_uuid=True)),
        sa.column("exercise_id", sa.Uuid(as_uuid=True)),
        sa.column("description", sa.String()),
    )
    if old_exercises:
        bind.execute(
            workout_exercises.insert(),
            [
                {
                    "id": uuid4(),
                    "workout_id": _uuid(row.workout_id),
                    "exercise_id": _uuid(row.exercise_id),
                    "description": _legacy_exercise_description(row),
                }
                for row in old_exercises
            ],
        )
    op.drop_table("workout_exercises")
    op.rename_table("_workout_exercises_new", "workout_exercises")
    op.create_index(
        "ix_workout_exercises_workout_id", "workout_exercises", ["workout_id"]
    )
    op.create_index(
        "ix_workout_exercises_exercise_id", "workout_exercises", ["exercise_id"]
    )

    old_logs = sa.table(
        "workout_logs",
        sa.column("id", sa.Uuid(as_uuid=True)),
        sa.column("user_id", sa.Uuid(as_uuid=True)),
        sa.column("workout_id", sa.Uuid(as_uuid=True)),
        sa.column("performed_on", sa.Date()),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    log_rows = bind.execute(
        sa.select(
            old_logs.c.id,
            old_logs.c.user_id,
            old_logs.c.workout_id,
            old_logs.c.performed_on,
            old_logs.c.created_at,
        )
    ).all()
    old_log_exercises = sa.table(
        "workout_log_exercises",
        sa.column("workout_log_id", sa.Uuid(as_uuid=True)),
        sa.column("exercise_id", sa.Uuid(as_uuid=True)),
        sa.column("sets", sa.Integer()),
        sa.column("reps", sa.Integer()),
        sa.column("weight_kg", sa.Float()),
        sa.column("exhaustion_level", sa.Integer()),
    )
    log_exercise_rows = bind.execute(
        sa.select(
            old_log_exercises.c.workout_log_id,
            old_log_exercises.c.exercise_id,
            old_log_exercises.c.sets,
            old_log_exercises.c.reps,
            old_log_exercises.c.weight_kg,
            old_log_exercises.c.exhaustion_level,
        )
    ).all()

    for row in log_rows:
        pair = (_uuid(row.user_id), _uuid(row.workout_id))
        if pair not in membership_ids:
            membership_id = uuid4()
            membership_ids[pair] = membership_id
            bind.execute(
                memberships.insert().values(
                    id=membership_id,
                    user_id=pair[0],
                    workout_id=pair[1],
                    owner=False,
                )
            )

    op.create_table(
        "workout_session",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("user_workout_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_workout_id"], ["user_workouts.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_workout_session_user_workout_id",
        "workout_session",
        ["user_workout_id"],
    )
    sessions = sa.table(
        "workout_session",
        sa.column("id", sa.Uuid(as_uuid=True)),
        sa.column("user_workout_id", sa.Uuid(as_uuid=True)),
        sa.column("date", sa.DateTime(timezone=True)),
    )
    for row in log_rows:
        performed_on = row.performed_on
        if not isinstance(performed_on, date):
            performed_on = date.fromisoformat(str(performed_on))
        bind.execute(
            sessions.insert().values(
                id=_uuid(row.id),
                user_workout_id=membership_ids[
                    (_uuid(row.user_id), _uuid(row.workout_id))
                ],
                date=datetime.combine(performed_on, time.min, tzinfo=timezone.utc),
            )
        )

    op.create_table(
        "workout_session_log",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("workout_session_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("exercise_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("weight", sa.Float(), nullable=True),
        sa.Column("reps", sa.Integer(), nullable=True),
        sa.Column("exhaustion_level", sa.Integer(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["workout_session_id"], ["workout_session.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercises.id"]),
    )
    op.create_index(
        "ix_workout_session_log_workout_session_id",
        "workout_session_log",
        ["workout_session_id"],
    )
    op.create_index(
        "ix_workout_session_log_exercise_id",
        "workout_session_log",
        ["exercise_id"],
    )
    session_logs = sa.table(
        "workout_session_log",
        sa.column("id", sa.Uuid(as_uuid=True)),
        sa.column("workout_session_id", sa.Uuid(as_uuid=True)),
        sa.column("exercise_id", sa.Uuid(as_uuid=True)),
        sa.column("weight", sa.Float()),
        sa.column("reps", sa.Integer()),
        sa.column("exhaustion_level", sa.Integer()),
        sa.column("timestamp", sa.DateTime(timezone=True)),
    )
    logs_by_session = {
        _uuid(row.id): row for row in log_rows
    }
    new_log_rows = []
    for row in log_exercise_rows:
        legacy_session_id = _uuid(row.workout_log_id)
        legacy_session = logs_by_session[legacy_session_id]
        created_at = legacy_session.created_at
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        for _ in range(max(row.sets or 1, 1)):
            new_log_rows.append(
                {
                    "id": uuid4(),
                    "workout_session_id": legacy_session_id,
                    "exercise_id": _uuid(row.exercise_id),
                    "weight": row.weight_kg,
                    "reps": row.reps,
                    "exhaustion_level": row.exhaustion_level,
                    "timestamp": created_at,
                }
            )
    if new_log_rows:
        bind.execute(session_logs.insert(), new_log_rows)

    op.drop_table("workout_log_exercises")
    op.drop_table("workout_logs")


def downgrade() -> None:
    raise NotImplementedError(
        "Workout sessions and individual set logs cannot be losslessly represented "
        "by the previous composite-key workout log schema."
    )
