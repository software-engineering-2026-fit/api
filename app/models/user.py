from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user_workout import UserWorkout

#Creating a end user table in the database
class User(SQLModel, table=True):
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(index=True, unique=True)
    name: str
    hashed_password: str
    is_admin: bool = Field(default=False, nullable=False)

    workout_links: list["UserWorkout"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "passive_deletes": True},
    )

#End user way to create a account
class UserCreate(SQLModel):
    email: str
    name: str
    password: str

#Api reply reading end user 
class UserRead(SQLModel):
    id: UUID
    email: str
    name: str
    is_admin: bool

class UserNewUsername(SQLModel):
    new_username: str
