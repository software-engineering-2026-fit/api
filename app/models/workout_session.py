from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user_workout import UserWorkout
    from app.models.workout_session_log import WorkoutSessionLog


class WorkoutSession(SQLModel, table=True):
    __tablename__ = "workout_session"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_workout_id: UUID = Field(
        foreign_key="user_workouts.id",
        index=True,
        nullable=False,
        ondelete="CASCADE",
    )
    date: datetime = Field(nullable=False, sa_type=DateTime(timezone=True))
    ended_at: datetime | None = Field(
        default=None,
        nullable=True,
        sa_type=DateTime(timezone=True),
    )

    user_workout: "UserWorkout" = Relationship(back_populates="sessions")
    logs: list["WorkoutSessionLog"] = Relationship(
        back_populates="workout_session",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "passive_deletes": True},
    )

class WorkoutSessionCreate(SQLModel):
    workout_id: UUID
    date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
    )
