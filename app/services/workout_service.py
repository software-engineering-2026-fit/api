from sqlmodel import Session, or_, select
from uuid import UUID

from app.models.exercise import Exercise
from app.models import (
    Exercise,
    Workout,
    WorkoutCreate,
    WorkoutExercise,
    WorkoutExerciseCreate,
    WorkoutExerciseRead,
    UserWorkout,
    WorkoutMemberRead,
    WorkoutLog,
    WorkoutLogCreate,
    WorkoutLogExercise,
    WorkoutLogExerciseRead,
    WorkoutLogRead,
)
from app.models.user import User


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
    return session.get(UserWorkout, (user_id, workout_id))


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


def list_workout_exercises(session: Session, workout_id: UUID) -> list[WorkoutExerciseRead]:
    rows = session.exec(
        select(WorkoutExercise, Exercise)
        .join(Exercise, Exercise.id == WorkoutExercise.exercise_id)
        .where(WorkoutExercise.workout_id == workout_id)
        .order_by(Exercise.name)
    ).all()
    return [
        WorkoutExerciseRead(
            exercise=exercise,
            sets=link.sets,
            reps=link.reps,
            weight_kg=link.weight_kg,
            exhaustion_level=link.exhaustion_level,
        )
        for link, exercise in rows
    ]


def add_exercise_to_workout(
    session: Session, workout_id: UUID, data: WorkoutExerciseCreate
) -> WorkoutExercise:
    link = session.get(WorkoutExercise, (workout_id, data.exercise_id))
    if link is None:
        link = WorkoutExercise(workout_id=workout_id, **data.model_dump())
    else:
        link.sets = data.sets
        link.reps = data.reps
        link.weight_kg = data.weight_kg
        link.exhaustion_level = data.exhaustion_level
    session.add(link)
    session.commit()
    session.refresh(link)
    return link


def remove_exercise_from_workout(
    session: Session, workout_id: UUID, exercise_id: UUID
) -> bool:
    link = session.get(WorkoutExercise, (workout_id, exercise_id))
    if link is None:
        return False
    session.delete(link)
    session.commit()
    return True


def list_workout_logs(session: Session, user_id: UUID) -> list[WorkoutLogRead]:
    rows = session.exec(
        select(WorkoutLog, Workout)
        .join(Workout, Workout.id == WorkoutLog.workout_id)
        .where(WorkoutLog.user_id == user_id)
        .order_by(
            WorkoutLog.performed_on.desc(),
            WorkoutLog.created_at.desc(),
            WorkoutLog.id.desc(),
        )
    ).all()
    return [
        _read_workout_log(session, workout_log, workout.name)
        for workout_log, workout in rows
    ]


def create_workout_log(
    session: Session, user_id: UUID, data: WorkoutLogCreate
) -> WorkoutLogRead:
    workout_log = WorkoutLog(
        user_id=user_id,
        workout_id=data.workout_id,
        performed_on=data.performed_on,
    )
    session.add(workout_log)
    session.flush()

    for exercise_data in data.exercises:
        session.add(
            WorkoutLogExercise(
                workout_log_id=workout_log.id,
                **exercise_data.model_dump(),
            )
        )

    session.commit()
    session.refresh(workout_log)
    workout = session.get(Workout, workout_log.workout_id)
    if workout is None:
        raise RuntimeError("The workout was deleted while saving its log.")
    return _read_workout_log(session, workout_log, workout.name)


def _read_workout_log(
    session: Session, workout_log: WorkoutLog, workout_name: str
) -> WorkoutLogRead:
    rows = session.exec(
        select(WorkoutLogExercise, Exercise)
        .join(Exercise, Exercise.id == WorkoutLogExercise.exercise_id)
        .where(WorkoutLogExercise.workout_log_id == workout_log.id)
        .order_by(Exercise.name)
    ).all()
    return WorkoutLogRead(
        id=workout_log.id,
        workout_id=workout_log.workout_id,
        workout_name=workout_name,
        performed_on=workout_log.performed_on,
        exercises=[
            WorkoutLogExerciseRead(
                exercise=exercise,
                sets=log_exercise.sets,
                reps=log_exercise.reps,
                weight_kg=log_exercise.weight_kg,
                exhaustion_level=log_exercise.exhaustion_level,
            )
            for log_exercise, exercise in rows
        ],
    )
