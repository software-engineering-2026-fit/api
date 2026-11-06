from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user_workout import UserWorkout


class WorkoutCreate(SQLModel):
    name: str
    description: str | None = None
    public: bool = False


class Workout(SQLModel, table=True):
    __tablename__ = "workouts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    description: str | None = None
    public: bool = Field(default=False, nullable=False)

    user_links: list["UserWorkout"] = Relationship(back_populates="workout")
