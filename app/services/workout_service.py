from sqlmodel import Session, select
from uuid import UUID

from app.models import Workout


def list_workouts(session: Session) -> list[Workout]:
    return list(session.exec(select(Workout)).all())


def get_workout(session: Session, workout_id: UUID) -> Workout | None:
    return session.get(Workout, workout_id)


def create_workout(session: Session, workout: Workout) -> Workout:
    session.add(workout)
    session.commit()
    session.refresh(workout)
    return workout
