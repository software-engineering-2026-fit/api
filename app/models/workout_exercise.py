from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from app.models.exercise import ExerciseRead

if TYPE_CHECKING:
    from app.models.exercise import Exercise
    from app.models.workout import Workout


# Link table: which exercises belong to which workout
class WorkoutExercise(SQLModel, table=True):
    __tablename__ = "workout_exercises"
    __table_args__ = (
        UniqueConstraint(
            "workout_id", "exercise_id", name="uq_workout_exercises_workout_exercise"
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    workout_id: UUID = Field(
        foreign_key="workouts.id", index=True, nullable=False, ondelete="CASCADE"
    )
    exercise_id: UUID = Field(
        foreign_key="exercises.id", index=True, nullable=False
    )
    description: str | None = None

    workout: "Workout" = Relationship(back_populates="exercise_links")
    exercise: "Exercise" = Relationship(back_populates="workout_links")


# Payload for adding an exercise to a workout
class WorkoutExerciseCreate(SQLModel):
    exercise_id: UUID
    description: str | None = None


# API response: exercise in a workout with its association description
class WorkoutExerciseRead(SQLModel):
    exercise: ExerciseRead
    description: str | None
