from app.models.user import UserCreate
from sqlmodel import Session, select

from app.models import User
from app.auth.security import hash_password, verify_password
from uuid import UUID


def list_users(session: Session) -> list[User]:
    return list(session.exec(select(User)).all())


def get_user(session: Session, user_id: UUID) -> User | None:
    return session.get(User, user_id)


def create_user(session: Session, user: UserCreate) -> User:
    db_user = User(
        email=user.email,
        name=user.name,
        hashed_password=hash_password(user.password),
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def authenticate_user(
    session: Session, email: str, password: str
) -> User | None:
    user = session.exec(select(User).where(User.email == email)).first()
    if (
        user is None
        or not user.hashed_password
        or not verify_password(password, user.hashed_password)
    ):
        return None
    return user
