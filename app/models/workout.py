from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.workout_exercise import WorkoutExercise
    from app.models.user_workout import UserWorkout


class WorkoutCreate(SQLModel):
    name: str
    description: str | None = None


class Workout(SQLModel, table=True):
    __tablename__ = "workouts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    description: str | None = None

    user_links: list["UserWorkout"] = Relationship(
        back_populates="workout",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "passive_deletes": True},
    )
    exercise_links: list["WorkoutExercise"] = Relationship(
        back_populates="workout",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "passive_deletes": True},
    )
