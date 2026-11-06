from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.auth.security import get_current_user
from app.db.database import get_session
from app.models import (
    User,
    WorkoutLogCreate,
    WorkoutLogRead,
    WorkoutExercise,
)
from app.services.workout_service import (
    create_workout_log,
    get_workout,
    get_workout_membership,
    list_workout_logs,
)

router = APIRouter(prefix="/workout-logs", tags=["workout-logs"])


@router.get("/", response_model=list[WorkoutLogRead])
def read_workout_logs(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> list[WorkoutLogRead]:
    return list_workout_logs(session, current_user.id)


@router.post(
    "/",
    response_model=WorkoutLogRead,
    status_code=status.HTTP_201_CREATED,
)
def add_workout_log(
    data: WorkoutLogCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> WorkoutLogRead:
    workout = get_workout(session, data.workout_id)
    if workout is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found",
        )
    if (
        not workout.public
        and get_workout_membership(session, data.workout_id, current_user.id) is None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found",
        )

    exercise_ids = [item.exercise_id for item in data.exercises]
    if len(exercise_ids) != len(set(exercise_ids)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Each exercise may only appear once in a workout log",
        )

    planned_exercise_ids = set(
        session.exec(
            select(WorkoutExercise.exercise_id).where(
                WorkoutExercise.workout_id == data.workout_id
            )
        ).all()
    )
    if not set(exercise_ids).issubset(planned_exercise_ids):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Workout logs can only include exercises from the selected workout",
        )

    return create_workout_log(session, current_user.id, data)
