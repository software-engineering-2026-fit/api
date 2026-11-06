from sqlmodel import Session, select
from uuid import UUID

from app.models import Exercise, Workout, WorkoutExercise, WorkoutExerciseCreate, WorkoutExerciseRead


def list_workouts(session: Session) -> list[Workout]:
    return list(session.exec(select(Workout)).all())


def get_workout(session: Session, workout_id: UUID) -> Workout | None:
    return session.get(Workout, workout_id)


def create_workout(session: Session, workout: Workout) -> Workout:
    session.add(workout)
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
