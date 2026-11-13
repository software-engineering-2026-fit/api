"""Workout session log models and schemas."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.exercise import Exercise
    from app.models.workout_session import WorkoutSession


class WorkoutSessionLog(SQLModel, table=True):
    __tablename__ = "workout_session_log"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    workout_session_id: UUID = Field(
        foreign_key="workout_session.id",
        index=True,
        nullable=False,
        ondelete="CASCADE",
    )
    exercise_id: UUID = Field(
        foreign_key="exercises.id", index=True, nullable=False
    )
    weight: float | None = None
    reps: int | None = None
    exhaustion_level: int | None = None
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_type=DateTime(timezone=True),
    )

    workout_session: "WorkoutSession" = Relationship(back_populates="logs")
    exercise: "Exercise" = Relationship(back_populates="session_logs")


class WorkoutSessionLogCreate(SQLModel):
    exercise_id: UUID
    weight: float | None = None
    reps: int | None = None
    exhaustion_level: int | None = None


class WorkoutSessionLogUpdate(SQLModel):
    weight: float | None = None
    reps: int | None = None
    exhaustion_level: int | None = None


class WorkoutSessionLogRead(SQLModel):
    id: UUID
    workout_session_id: UUID
    exercise_id: UUID
    exercise_name: str
    weight: float | None
    reps: int | None
    exhaustion_level: int | None
    timestamp: datetime


class WorkoutSessionRead(SQLModel):
    id: UUID
    user_workout_id: UUID
    date: datetime
    ended_at: datetime | None
    logs: list[WorkoutSessionLogRead]