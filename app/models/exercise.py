from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class ExerciseBase(SQLModel):
    name: str = Field(index=True)
    description: str | None = None
    muscle_group: str | None = Field(default=None, index=True)
    equipment: str | None = Field(default=None, index=True)


# Exercise catalog table in the database
class Exercise(ExerciseBase, table=True):
    __tablename__ = "exercises"

    id: UUID = Field(default_factory=uuid4, primary_key=True)


# Payload for creating an exercise
class ExerciseCreate(ExerciseBase):
    pass


# API response for reading an exercise
class ExerciseRead(ExerciseBase):
    id: UUID
