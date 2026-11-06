from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.auth.security import get_current_user
from app.db.database import get_session
from app.models import Exercise, ExerciseCreate, ExerciseRead, User
from app.services.exercise_service import (
    create_exercise,
    get_exercise,
    search_exercises,
)

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("/", response_model=list[ExerciseRead])
def read_exercises(
    _: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
    q: Annotated[
        str | None,
        Query(max_length=100, description="Search in name, description, muscle group, and equipment"),
    ] = None,
    muscle_group: Annotated[str | None, Query(max_length=50)] = None,
    equipment: Annotated[str | None, Query(max_length=50)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[Exercise]:
    return search_exercises(session, q, muscle_group, equipment, limit, offset)


@router.get("/{exercise_id}", response_model=ExerciseRead)
def read_exercise(
    exercise_id: UUID,
    _: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> Exercise:
    exercise = get_exercise(session, exercise_id)
    if exercise is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found",
        )
    return exercise


@router.post("/", response_model=ExerciseRead, status_code=status.HTTP_201_CREATED)
def add_exercise(
    exercise: ExerciseCreate,
    _: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> Exercise:
    return create_exercise(session, exercise)
