from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.auth.security import get_current_user
from app.db.database import get_session
from app.models import (
    User,
    Workout,
    WorkoutCreate,
    WorkoutExerciseCreate,
    WorkoutExerciseRead,
    WorkoutMemberRead,
)
from app.services.exercise_service import get_exercise
from app.services.workout_service import (
    add_exercise_to_workout,
    create_workout,
    get_workout,
    get_workout_membership,
    list_workout_exercises,
    list_workout_members,
    list_workouts,
    remove_exercise_from_workout,
)

router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.get("/", response_model=list[Workout])
def read_workouts(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> list[Workout]:
    return list_workouts(session, current_user.id)


@router.get("/{workout_id}", response_model=Workout)
def read_workout(
    workout_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> Workout:
    workout = _get_workout_or_404(session, workout_id)
    if get_workout_membership(session, workout_id, current_user.id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")
    return workout


@router.post("/", response_model=Workout, status_code=status.HTTP_201_CREATED)
def add_workout(
    workout: WorkoutCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> Workout:
    return create_workout(session, workout, current_user.id)


@router.get("/{workout_id}/users", response_model=list[WorkoutMemberRead])
def read_workout_users(
    workout_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> list[WorkoutMemberRead]:
    _get_own_workout_or_404(session, workout_id, current_user)
    return list_workout_members(session, workout_id)


def _get_workout_or_404(session: Session, workout_id: UUID) -> Workout:
    workout = get_workout(session, workout_id)
    if workout is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")
    return workout


def _get_own_workout_or_404(session: Session, workout_id: UUID, user: User) -> Workout:
    workout = _get_workout_or_404(session, workout_id)
    membership = get_workout_membership(session, workout_id, user.id)
    if membership is None or not membership.owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your workout")
    return workout


def _get_accessible_workout_or_404(
    session: Session, workout_id: UUID, user: User
) -> Workout:
    workout = _get_workout_or_404(session, workout_id)
    if get_workout_membership(session, workout_id, user.id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")
    return workout


@router.get("/{workout_id}/exercises", response_model=list[WorkoutExerciseRead])
def read_workout_exercises(
    workout_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> list[WorkoutExerciseRead]:
    _get_accessible_workout_or_404(session, workout_id, current_user)
    return list_workout_exercises(session, workout_id)


@router.post(
    "/{workout_id}/exercises",
    response_model=list[WorkoutExerciseRead],
    status_code=status.HTTP_201_CREATED,
)
def add_workout_exercise(
    workout_id: UUID,
    data: WorkoutExerciseCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> list[WorkoutExerciseRead]:
    _get_own_workout_or_404(session, workout_id, current_user)
    if get_exercise(session, data.exercise_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")
    add_exercise_to_workout(session, workout_id, data)
    return list_workout_exercises(session, workout_id)


@router.delete("/{workout_id}/exercises/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout_exercise(
    workout_id: UUID,
    exercise_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> None:
    _get_own_workout_or_404(session, workout_id, current_user)
    if not remove_exercise_from_workout(session, workout_id, exercise_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not in workout")
