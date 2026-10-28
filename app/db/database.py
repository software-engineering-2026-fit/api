import os
from collections.abc import Generator

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, create_engine

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

is_sqlite = DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}
engine_kwargs = {"connect_args": connect_args}
if DATABASE_URL == "sqlite://":
    engine_kwargs["poolclass"] = StaticPool

engine = create_engine(DATABASE_URL, echo=False, **engine_kwargs)

#Creating a engine connecting Docker connection and database setup
def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
