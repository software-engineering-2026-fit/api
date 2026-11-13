from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.workout import Workout
    from app.models.workout_session import WorkoutSession


class UserWorkout(SQLModel, table=True):
    __tablename__ = "user_workouts"
    __table_args__ = (
        UniqueConstraint("user_id", "workout_id", name="uq_user_workouts_user_workout"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(
        foreign_key="users.id", index=True, nullable=False, ondelete="CASCADE"
    )
    workout_id: UUID = Field(
        foreign_key="workouts.id", index=True, nullable=False, ondelete="CASCADE"
    )
    owner: bool = Field(default=False, nullable=False)

    user: "User" = Relationship(back_populates="workout_links")
    workout: "Workout" = Relationship(back_populates="user_links")
    sessions: list["WorkoutSession"] = Relationship(
        back_populates="user_workout",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "passive_deletes": True},
    )


class WorkoutMemberRead(SQLModel):
    user_id: UUID
    name: str
    email: str
    owner: bool