from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session, select

from app.auth.security import get_current_user
from app.db.database import get_session
from app.models import (
    User,
    WorkoutExercise,
    WorkoutSession,
    WorkoutSessionCreate,
    WorkoutSessionLogCreate,
    WorkoutSessionLogRead,
    WorkoutSessionLogUpdate,
    WorkoutSessionRead,
)
from app.services.workout_service import (
    create_workout_session,
    create_workout_session_log,
    delete_workout_session_log,
    end_workout_session,
    get_workout,
    get_workout_membership,
    get_workout_session,
    get_workout_session_log,
    get_workout_for_session,
    list_workout_session_logs,
    list_workout_sessions,
    update_workout_session_log,
)

router = APIRouter(prefix="/workout-sessions", tags=["workout-sessions"])


@router.get("/", response_model=list[WorkoutSessionRead])
def read_workout_sessions(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> list[WorkoutSessionRead]:
    return [
        _read_session(session, item)
        for item in list_workout_sessions(session, current_user.id)
    ]


@router.post(
    "/", response_model=WorkoutSessionRead, status_code=status.HTTP_201_CREATED
)
def add_workout_session(
    data: WorkoutSessionCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> WorkoutSessionRead:
    workout = get_workout(session, data.workout_id)
    membership = get_workout_membership(session, data.workout_id, current_user.id)
    if workout is None or membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")
    workout_session = create_workout_session(session, membership.id, data)
    return _read_session(session, workout_session)


@router.get("/{session_id}", response_model=WorkoutSessionRead)
def read_workout_session(
    session_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> WorkoutSessionRead:
    return _read_session(session, _get_session_or_404(session, session_id, current_user))


@router.post("/{session_id}/end", response_model=WorkoutSessionRead)
def finish_workout_session(
    session_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> WorkoutSessionRead:
    workout_session = _get_session_or_404(session, session_id, current_user)
    return _read_session(session, end_workout_session(session, workout_session))


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout_session(
    session_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> Response:
    workout_session = _get_session_or_404(session, session_id, current_user)
    session.delete(workout_session)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{session_id}/logs", response_model=list[WorkoutSessionLogRead])
def read_workout_session_logs(
    session_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> list[WorkoutSessionLogRead]:
    workout_session = _get_session_or_404(session, session_id, current_user)
    return list_workout_session_logs(session, workout_session.id)


@router.post(
    "/{session_id}/logs",
    response_model=WorkoutSessionLogRead,
    status_code=status.HTTP_201_CREATED,
)
def add_workout_session_log(
    session_id: UUID,
    data: WorkoutSessionLogCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> WorkoutSessionLogRead:
    workout_session = _get_session_or_404(session, session_id, current_user)
    if workout_session.ended_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot add logs to an ended workout session",
        )
    workout = get_workout_for_session(session, workout_session)
    if workout is None or session.exec(
        select(WorkoutExercise.id).where(
            WorkoutExercise.workout_id == workout.id,
            WorkoutExercise.exercise_id == data.exercise_id,
        )
    ).first() is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Session logs can only include exercises from the session workout",
        )
    return create_workout_session_log(session, workout_session.id, data)


@router.patch(
    "/{session_id}/logs/{log_id}", response_model=WorkoutSessionLogRead
)
def edit_workout_session_log(
    session_id: UUID,
    log_id: UUID,
    data: WorkoutSessionLogUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> WorkoutSessionLogRead:
    workout_session = _get_session_or_404(session, session_id, current_user)
    log_and_exercise = get_workout_session_log(
        session, log_id, workout_session.id
    )
    if log_and_exercise is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session log not found")
    workout_log, _ = log_and_exercise
    return update_workout_session_log(session, workout_log, data)


@router.delete(
    "/{session_id}/logs/{log_id}", status_code=status.HTTP_204_NO_CONTENT
)
def remove_workout_session_log(
    session_id: UUID,
    log_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> Response:
    workout_session = _get_session_or_404(session, session_id, current_user)
    log_and_exercise = get_workout_session_log(
        session, log_id, workout_session.id
    )
    if log_and_exercise is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session log not found")
    workout_log, _ = log_and_exercise
    delete_workout_session_log(session, workout_log)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _get_session_or_404(
    session: Session, session_id: UUID, user: User
) -> WorkoutSession:
    workout_session = get_workout_session(session, session_id, user.id)
    if workout_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout session not found",
        )
    return workout_session


def _read_session(
    session: Session, workout_session: WorkoutSession
) -> WorkoutSessionRead:
    workout = get_workout_for_session(session, workout_session)
    if workout is None:
        raise RuntimeError("The workout for this session could not be found.")

    return WorkoutSessionRead(
        id=workout_session.id,
        user_workout_id=workout_session.user_workout_id,
        workout_id=workout.id,
        workout_name=workout.name,
        date=workout_session.date,
        ended_at=workout_session.ended_at,
        logs=list_workout_session_logs(session, workout_session.id),
    )
