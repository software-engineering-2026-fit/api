from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from app.models.exercise import ExerciseRead


class WorkoutLogExerciseCreate(SQLModel):
    exercise_id: UUID
    sets: int = Field(ge=1)
    reps: int = Field(ge=1)
    weight_kg: float | None = Field(default=None, ge=0)
    exhaustion_level: int | None = Field(default=None, ge=1, le=5)


class WorkoutLogCreate(SQLModel):
    workout_id: UUID
    performed_on: date
    exercises: list[WorkoutLogExerciseCreate] = Field(min_length=1)


class WorkoutLog(SQLModel, table=True):
    __tablename__ = "workout_logs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True, ondelete="CASCADE")
    workout_id: UUID = Field(foreign_key="workouts.id", index=True, ondelete="CASCADE")
    performed_on: date
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WorkoutLogExercise(SQLModel, table=True):
    __tablename__ = "workout_log_exercises"

    workout_log_id: UUID = Field(
        foreign_key="workout_logs.id", primary_key=True, ondelete="CASCADE"
    )
    exercise_id: UUID = Field(
        foreign_key="exercises.id", primary_key=True, ondelete="CASCADE"
    )
    sets: int = Field(ge=1)
    reps: int = Field(ge=1)
    weight_kg: float | None = Field(default=None, ge=0)
    exhaustion_level: int | None = Field(default=None, ge=1, le=5)


class WorkoutLogExerciseRead(SQLModel):
    exercise: ExerciseRead
    sets: int
    reps: int
    weight_kg: float | None
    exhaustion_level: int | None


class WorkoutLogRead(SQLModel):
    id: UUID
    workout_id: UUID
    workout_name: str
    performed_on: date
    exercises: list[WorkoutLogExerciseRead]
