from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.auth.security import get_current_user
from app.db.database import get_session
from app.models import User, UserRead
from app.services.user_service import get_user, list_users

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserRead])
def read_users(
    _: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> list[User]:
    return list_users(session)


@router.get("/{user_id}", response_model=UserRead)
def read_user(
    user_id: UUID,
    _: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> User:
    user = get_user(session, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user
