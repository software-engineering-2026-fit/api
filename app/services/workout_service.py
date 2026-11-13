from uuid import UUID

from datetime import datetime, timezone

from sqlmodel import Session, or_, select

from app.models import (
    Exercise,
    User,
    UserWorkout,
    Workout,
    WorkoutCreate,
    WorkoutExercise,
    WorkoutExerciseCreate,
    WorkoutExerciseRead,
    WorkoutMemberRead,
    WorkoutSession,
    WorkoutSessionCreate,
    WorkoutSessionLog,
    WorkoutSessionLogCreate,
    WorkoutSessionLogRead,
    WorkoutSessionLogUpdate,
)


def list_workouts(session: Session, user_id: UUID) -> list[Workout]:
    statement = (
        select(Workout)
        .outerjoin(UserWorkout, UserWorkout.workout_id == Workout.id)
        .where(or_(Workout.public.is_(True), UserWorkout.user_id == user_id))
        .distinct()
    )
    return list(session.exec(statement).all())


def list_public_workouts(session: Session) -> list[Workout]:
    statement = (
        select(Workout)
        .where(Workout.public.is_(True))
        .order_by(Workout.name)
    )
    return list(session.exec(statement).all())


def get_workout(session: Session, workout_id: UUID) -> Workout | None:
    return session.get(Workout, workout_id)


def get_workout_membership(
    session: Session, workout_id: UUID, user_id: UUID
) -> UserWorkout | None:
    return session.exec(
        select(UserWorkout).where(
            UserWorkout.user_id == user_id,
            UserWorkout.workout_id == workout_id,
        )
    ).first()


def get_or_create_workout_membership(
    session: Session, workout_id: UUID, user_id: UUID
) -> UserWorkout:
    membership = get_workout_membership(session, workout_id, user_id)
    if membership is not None:
        return membership
    membership = UserWorkout(
        user_id=user_id,
        workout_id=workout_id,
        owner=False,
    )
    session.add(membership)
    session.flush()
    return membership


def list_workout_members(
    session: Session, workout_id: UUID
) -> list[WorkoutMemberRead]:
    rows = session.exec(
        select(UserWorkout, User)
        .join(User, User.id == UserWorkout.user_id)
        .where(UserWorkout.workout_id == workout_id)
        .order_by(User.name)
    ).all()
    return [
        WorkoutMemberRead(
            user_id=user.id,
            name=user.name,
            email=user.email,
            owner=membership.owner,
        )
        for membership, user in rows
    ]


def create_workout(
    session: Session, workout_data: WorkoutCreate, user_id: UUID
) -> Workout:
    workout = Workout(
        name=workout_data.name,
        description=workout_data.description,
        public=workout_data.public,
    )
    session.add(workout)
    session.flush()
    session.add(
        UserWorkout(user_id=user_id, workout_id=workout.id, owner=True)
    )
    session.commit()
    session.refresh(workout)
    return workout


def list_workout_exercises(
    session: Session, workout_id: UUID
) -> list[WorkoutExerciseRead]:
    rows = session.exec(
        select(WorkoutExercise, Exercise)
        .join(Exercise, Exercise.id == WorkoutExercise.exercise_id)
        .where(WorkoutExercise.workout_id == workout_id)
        .order_by(Exercise.name)
    ).all()
    return [
        WorkoutExerciseRead(exercise=exercise, description=link.description)
        for link, exercise in rows
    ]


def _get_workout_exercise(
    session: Session, workout_id: UUID, exercise_id: UUID
) -> WorkoutExercise | None:
    return session.exec(
        select(WorkoutExercise).where(
            WorkoutExercise.workout_id == workout_id,
            WorkoutExercise.exercise_id == exercise_id,
        )
    ).first()


def add_exercise_to_workout(
    session: Session, workout_id: UUID, data: WorkoutExerciseCreate
) -> WorkoutExercise:
    link = _get_workout_exercise(session, workout_id, data.exercise_id)
    if link is None:
        link = WorkoutExercise(workout_id=workout_id, **data.model_dump())
    else:
        link.description = data.description
    session.add(link)
    session.commit()
    session.refresh(link)
    return link


def remove_exercise_from_workout(
    session: Session, workout_id: UUID, exercise_id: UUID
) -> bool:
    link = _get_workout_exercise(session, workout_id, exercise_id)
    if link is None:
        return False
    session.delete(link)
    session.commit()
    return True


def create_workout_session(
    session: Session, user_workout_id: UUID, data: WorkoutSessionCreate
) -> WorkoutSession:
    workout_session = WorkoutSession(
        user_workout_id=user_workout_id,
        date=data.date,
    )
    session.add(workout_session)
    session.commit()
    session.refresh(workout_session)
    return workout_session


def end_workout_session(
    session: Session, workout_session: WorkoutSession
) -> WorkoutSession:
    if workout_session.ended_at is None:
        workout_session.ended_at = datetime.now(timezone.utc)
        session.add(workout_session)
        session.commit()
        session.refresh(workout_session)
    return workout_session


def get_workout_session(
    session: Session, session_id: UUID, user_id: UUID
) -> WorkoutSession | None:
    return session.exec(
        select(WorkoutSession)
        .join(UserWorkout, UserWorkout.id == WorkoutSession.user_workout_id)
        .where(
            WorkoutSession.id == session_id,
            UserWorkout.user_id == user_id,
        )
    ).first()


def list_workout_sessions(session: Session, user_id: UUID) -> list[WorkoutSession]:
    statement = (
        select(WorkoutSession)
        .join(UserWorkout, UserWorkout.id == WorkoutSession.user_workout_id)
        .where(UserWorkout.user_id == user_id)
        .order_by(WorkoutSession.date.desc(), WorkoutSession.id.desc())
    )
    return list(session.exec(statement).all())


def list_workout_session_logs(
    session: Session, workout_session_id: UUID
) -> list[WorkoutSessionLogRead]:
    rows = session.exec(
        select(WorkoutSessionLog, Exercise)
        .join(Exercise, Exercise.id == WorkoutSessionLog.exercise_id)
        .where(WorkoutSessionLog.workout_session_id == workout_session_id)
        .order_by(WorkoutSessionLog.timestamp, WorkoutSessionLog.id)
    ).all()
    return [
        _read_workout_session_log(log, exercise)
        for log, exercise in rows
    ]


def _read_workout_session_log(
    workout_log: WorkoutSessionLog, exercise: Exercise
) -> WorkoutSessionLogRead:
    return WorkoutSessionLogRead(
        id=workout_log.id,
        workout_session_id=workout_log.workout_session_id,
        exercise_id=workout_log.exercise_id,
        exercise_name=exercise.name,
        weight=workout_log.weight,
        reps=workout_log.reps,
        exhaustion_level=workout_log.exhaustion_level,
        timestamp=workout_log.timestamp,
    )


def get_workout_session_log(
    session: Session, log_id: UUID, workout_session_id: UUID
) -> tuple[WorkoutSessionLog, Exercise] | None:
    return session.exec(
        select(WorkoutSessionLog, Exercise)
        .join(Exercise, Exercise.id == WorkoutSessionLog.exercise_id)
        .where(
            WorkoutSessionLog.id == log_id,
            WorkoutSessionLog.workout_session_id == workout_session_id,
        )
    ).first()


def create_workout_session_log(
    session: Session,
    workout_session_id: UUID,
    data: WorkoutSessionLogCreate,
) -> WorkoutSessionLogRead:
    workout_log = WorkoutSessionLog(
        workout_session_id=workout_session_id,
        **data.model_dump(),
    )
    session.add(workout_log)
    session.commit()
    session.refresh(workout_log)
    exercise = session.get(Exercise, workout_log.exercise_id)
    if exercise is None:
        raise RuntimeError("The exercise was deleted while saving its session log.")
    return _read_workout_session_log(workout_log, exercise)


def update_workout_session_log(
    session: Session,
    workout_log: WorkoutSessionLog,
    data: WorkoutSessionLogUpdate,
) -> WorkoutSessionLogRead:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(workout_log, field, value)
    session.add(workout_log)
    session.commit()
    session.refresh(workout_log)
    exercise = session.get(Exercise, workout_log.exercise_id)
    if exercise is None:
        raise RuntimeError("The exercise for this session log no longer exists.")
    return _read_workout_session_log(workout_log, exercise)


def delete_workout_session_log(session: Session, workout_log: WorkoutSessionLog) -> None:
    session.delete(workout_log)
    session.commit()


def get_workout_for_session(
    session: Session, workout_session: WorkoutSession
) -> Workout | None:
    membership = session.get(UserWorkout, workout_session.user_workout_id)
    if membership is None:
        return None
    return session.get(Workout, membership.workout_id)
