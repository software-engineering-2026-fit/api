from uuid import UUID

from sqlmodel import Session, col, or_, select

from app.models import Exercise, ExerciseCreate


def search_exercises(
    session: Session,
    query: str | None = None,
    muscle_group: str | None = None,
    equipment: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Exercise]:
    statement = select(Exercise)

    if query:
        pattern = f"%{query.strip()}%"
        statement = statement.where(
            or_(
                col(Exercise.name).ilike(pattern),
                col(Exercise.description).ilike(pattern),
                col(Exercise.muscle_group).ilike(pattern),
                col(Exercise.equipment).ilike(pattern),
            )
        )
    if muscle_group:
        statement = statement.where(col(Exercise.muscle_group).ilike(muscle_group.strip()))
    if equipment:
        statement = statement.where(col(Exercise.equipment).ilike(equipment.strip()))

    statement = statement.order_by(Exercise.name).offset(offset).limit(limit)
    return list(session.exec(statement).all())


def get_exercise(session: Session, exercise_id: UUID) -> Exercise | None:
    return session.get(Exercise, exercise_id)


def create_exercise(session: Session, exercise: ExerciseCreate) -> Exercise:
    db_exercise = Exercise.model_validate(exercise)
    session.add(db_exercise)
    session.commit()
    session.refresh(db_exercise)
    return db_exercise
