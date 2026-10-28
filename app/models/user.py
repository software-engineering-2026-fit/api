from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.workout import Workout

#Creating a end user table in the database
class User(SQLModel, table=True):
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(index=True, unique=True)
    name: str
    hashed_password: str

    workouts: list["Workout"] = Relationship(back_populates="user")

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
