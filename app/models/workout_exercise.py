from uuid import UUID

from sqlmodel import Field, SQLModel

from app.models.exercise import ExerciseRead


# Link table: which exercises belong to which workout
class WorkoutExercise(SQLModel, table=True):
    __tablename__ = "workout_exercises"

    workout_id: UUID = Field(foreign_key="workouts.id", primary_key=True, ondelete="CASCADE")
    exercise_id: UUID = Field(foreign_key="exercises.id", primary_key=True, ondelete="CASCADE")
    sets: int | None = Field(default=None, ge=1)
    reps: int | None = Field(default=None, ge=1)
    weight_kg: float | None = Field(default=None, ge=0)
    exhaustion_level: int | None = Field(default=None, ge=1, le=5)


# Payload for adding an exercise to a workout
class WorkoutExerciseCreate(SQLModel):
    exercise_id: UUID
    sets: int | None = Field(default=None, ge=1)
    reps: int = Field(ge=1)
    weight_kg: float = Field(ge=0)
    exhaustion_level: int | None = Field(default=None, ge=1, le=5)


# API response: exercise in a workout with its sets/reps
class WorkoutExerciseRead(SQLModel):
    exercise: ExerciseRead
    sets: int | None
    reps: int | None
    weight_kg: float | None
    exhaustion_level: int | None
