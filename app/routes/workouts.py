from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.auth.security import get_current_user
from app.db.database import get_session
from app.models import User, Workout
from app.services.workout_service import create_workout, get_workout, list_workouts

router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.get("/", response_model=list[Workout])
def read_workouts(
    _: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> list[Workout]:
    return list_workouts(session)


@router.get("/{workout_id}", response_model=Workout)
def read_workout(
    workout_id: UUID,
    _: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> Workout:
    workout = get_workout(session, workout_id)
    if workout is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found",
        )
    return workout


@router.post("/", response_model=Workout, status_code=status.HTTP_201_CREATED)
def add_workout(
    workout: Workout,
    _: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> Workout:
    return create_workout(session, workout)
