from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.workout import Workout


class UserWorkout(SQLModel, table=True):
    __tablename__ = "user_workouts"

    user_id: UUID = Field(
        foreign_key="users.id", primary_key=True, ondelete="CASCADE"
    )
    workout_id: UUID = Field(
        foreign_key="workouts.id", primary_key=True, ondelete="CASCADE"
    )
    owner: bool = Field(default=False, nullable=False)

    user: "User" = Relationship(back_populates="workout_links")
    workout: "Workout" = Relationship(back_populates="user_links")


class WorkoutMemberRead(SQLModel):
    user_id: UUID
    name: str
    email: str
    owner: bool