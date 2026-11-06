from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import User


class WorkoutCreate(SQLModel):
    name: str
    description: str | None = None


class Workout(SQLModel, table=True):
    __tablename__ = "workouts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    description: str | None = None
    user_id: UUID = Field(foreign_key="users.id", index=True)

    user: "User" = Relationship(back_populates="workouts")
