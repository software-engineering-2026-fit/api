from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.workout_exercise import WorkoutExercise
    from app.models.workout_session import WorkoutSessionLog


class ExerciseBase(SQLModel):
    name: str = Field(index=True)
    description: str | None = None
    muscle_group: str | None = Field(default=None, index=True)
    equipment: str | None = Field(default=None, index=True)


# Exercise catalog table in the database
class Exercise(ExerciseBase, table=True):
    __tablename__ = "exercises"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    workout_links: list["WorkoutExercise"] = Relationship(back_populates="exercise")
    session_logs: list["WorkoutSessionLog"] = Relationship(back_populates="exercise")


# Payload for creating an exercise
class ExerciseCreate(ExerciseBase):
    pass


# API response for reading an exercise
class ExerciseRead(ExerciseBase):
    id: UUID
