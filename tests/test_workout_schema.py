import unittest
from datetime import datetime, timezone
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import event, inspect
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.models import (
    Exercise,
    User,
    UserWorkout,
    Workout,
    WorkoutExercise,
    WorkoutSession,
    WorkoutSessionLog,
    WorkoutSessionLogUpdate,
)
from app.auth.security import get_current_user
from app.db.database import get_session
from app.main import app
from app.services.workout_service import (
    delete_workout_session_log,
    get_workout_session_log,
    update_workout_session_log,
)


class WorkoutSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        @event.listens_for(self.engine, "connect")
        def enable_foreign_keys(connection, _) -> None:
            connection.execute("PRAGMA foreign_keys=ON")

        SQLModel.metadata.create_all(self.engine)
        self.session = Session(self.engine)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        self.session.close()
        self.engine.dispose()

    def test_target_tables_use_uuid_primary_keys_and_index_foreign_keys(self) -> None:
        expected_tables = {
            "users",
            "workouts",
            "user_workouts",
            "workout_session",
            "exercises",
            "workout_exercises",
            "workout_session_log",
        }
        self.assertEqual(set(SQLModel.metadata.tables), expected_tables)
        expected_columns = {
            "users": {"id", "email", "name", "hashed_password", "is_admin"},
            "workouts": {"id", "name", "public", "description"},
            "user_workouts": {"id", "user_id", "workout_id", "owner"},
            "workout_session": {"id", "user_workout_id", "date", "ended_at"},
            "exercises": {
                "id",
                "name",
                "description",
                "muscle_group",
                "equipment",
            },
            "workout_exercises": {
                "id",
                "workout_id",
                "exercise_id",
                "description",
            },
            "workout_session_log": {
                "id",
                "workout_session_id",
                "exercise_id",
                "weight",
                "reps",
                "exhaustion_level",
                "timestamp",
            },
        }

        inspector = inspect(self.engine)
        for table_name in expected_tables:
            table = SQLModel.metadata.tables[table_name]
            self.assertEqual(set(table.columns.keys()), expected_columns[table_name])
            primary_key = list(table.primary_key.columns)
            self.assertEqual([column.name for column in primary_key], ["id"])
            self.assertIs(primary_key[0].type.python_type, UUID)

            indexed_columns = {
                column_name
                for index in inspector.get_indexes(table_name)
                for column_name in index["column_names"]
            }
            for foreign_key in inspector.get_foreign_keys(table_name):
                self.assertIn(foreign_key["constrained_columns"][0], indexed_columns)

        expected_foreign_keys = {
            "user_workouts": {
                ("user_id", "users", "id"),
                ("workout_id", "workouts", "id"),
            },
            "workout_session": {
                ("user_workout_id", "user_workouts", "id"),
            },
            "workout_exercises": {
                ("workout_id", "workouts", "id"),
                ("exercise_id", "exercises", "id"),
            },
            "workout_session_log": {
                ("workout_session_id", "workout_session", "id"),
                ("exercise_id", "exercises", "id"),
            },
        }
        for table_name, expected in expected_foreign_keys.items():
            actual = {
                (
                    foreign_key["constrained_columns"][0],
                    foreign_key["referred_table"],
                    foreign_key["referred_columns"][0],
                )
                for foreign_key in inspector.get_foreign_keys(table_name)
            }
            self.assertEqual(actual, expected)

    def test_associations_and_multiple_independent_logs(self) -> None:
        user = User(email="user@example.com", name="User", hashed_password="hash")
        other_user = User(
            email="other@example.com", name="Other User", hashed_password="hash"
        )
        workout = Workout(name="Strength", public=False)
        another_workout = Workout(name="Cardio", public=False)
        exercise = Exercise(name="Bench Press")
        self.session.add_all([user, other_user, workout, another_workout, exercise])
        self.session.flush()

        owner_link = UserWorkout(
            user_id=user.id, workout_id=workout.id, owner=True
        )
        shared_link = UserWorkout(
            user_id=other_user.id, workout_id=workout.id, owner=False
        )
        another_user_workout = UserWorkout(
            user_id=user.id, workout_id=another_workout.id, owner=True
        )
        exercise_link = WorkoutExercise(
            workout_id=workout.id,
            exercise_id=exercise.id,
            description="Controlled tempo",
        )
        another_exercise_link = WorkoutExercise(
            workout_id=another_workout.id,
            exercise_id=exercise.id,
        )
        workout_session = WorkoutSession(
            user_workout=owner_link,
            date=datetime(2026, 11, 13, tzinfo=timezone.utc),
        )
        first_log = WorkoutSessionLog(
            workout_session=workout_session,
            exercise_id=exercise.id,
            reps=8,
            weight=40,
        )
        second_log = WorkoutSessionLog(
            workout_session=workout_session,
            exercise_id=exercise.id,
            reps=6,
            weight=45,
        )
        self.session.add_all(
            [
                owner_link,
                shared_link,
                another_user_workout,
                exercise_link,
                another_exercise_link,
                workout_session,
                first_log,
                second_log,
            ]
        )
        self.session.commit()

        self.assertNotEqual(first_log.id, second_log.id)
        self.assertEqual(
            len(
                self.session.exec(
                    select(WorkoutSessionLog).where(
                        WorkoutSessionLog.exercise_id == exercise.id
                    )
                ).all()
            ),
            2,
        )
        self.assertEqual(len(workout.user_links), 2)
        self.assertEqual(len(workout.exercise_links), 1)
        self.assertEqual(len(user.workout_links), 2)
        self.assertEqual(len(exercise.workout_links), 2)

        log_row = get_workout_session_log(
            self.session, first_log.id, workout_session.id
        )
        self.assertIsNotNone(log_row)
        updated = update_workout_session_log(
            self.session, log_row[0], WorkoutSessionLogUpdate(reps=9)
        )
        self.assertEqual(updated.reps, 9)

        log_row = get_workout_session_log(
            self.session, first_log.id, workout_session.id
        )
        delete_workout_session_log(self.session, log_row[0])
        self.assertIsNone(self.session.get(WorkoutSessionLog, first_log.id))
        self.assertIsNotNone(self.session.get(WorkoutSessionLog, second_log.id))
        self.assertIsNotNone(self.session.get(Exercise, exercise.id))

    def test_deleting_workout_cascades_associations_not_shared_exercises(self) -> None:
        user = User(email="user@example.com", name="User", hashed_password="hash")
        workout = Workout(name="Shared")
        exercise = Exercise(name="Squat")
        self.session.add_all([user, workout, exercise])
        self.session.flush()
        membership = UserWorkout(
            user_id=user.id, workout_id=workout.id, owner=True
        )
        session_row = WorkoutSession(
            user_workout=membership,
            date=datetime.now(timezone.utc),
        )
        self.session.add_all(
            [
                membership,
                WorkoutExercise(workout_id=workout.id, exercise_id=exercise.id),
                session_row,
                WorkoutSessionLog(
                    workout_session=session_row,
                    exercise_id=exercise.id,
                ),
            ]
        )
        self.session.commit()
        workout_id = workout.id
        exercise_id = exercise.id
        user_id = user.id

        self.session.delete(workout)
        self.session.commit()

        self.assertIsNone(self.session.get(Workout, workout_id))
        self.assertIsNotNone(self.session.get(Exercise, exercise_id))
        self.assertIsNotNone(self.session.get(User, user_id))
        self.assertEqual(self.session.exec(select(UserWorkout)).all(), [])
        self.assertEqual(self.session.exec(select(WorkoutExercise)).all(), [])
        self.assertEqual(self.session.exec(select(WorkoutSession)).all(), [])
        self.assertEqual(self.session.exec(select(WorkoutSessionLog)).all(), [])

    def test_session_and_individual_log_endpoints(self) -> None:
        user = User(email="api@example.com", name="API User", hashed_password="hash")
        workout = Workout(name="API Workout")
        exercise = Exercise(name="API Exercise")
        self.session.add_all([user, workout, exercise])
        self.session.flush()
        membership = UserWorkout(
            user_id=user.id, workout_id=workout.id, owner=True
        )
        self.session.add_all(
            [
                membership,
                WorkoutExercise(workout_id=workout.id, exercise_id=exercise.id),
            ]
        )
        self.session.commit()
        user_id = user.id
        workout_id = workout.id
        exercise_id = exercise.id

        def current_user_override() -> User:
            return self.session.get(User, user_id)

        def session_override():
            with Session(self.engine) as request_session:
                yield request_session

        app.dependency_overrides[get_current_user] = current_user_override
        app.dependency_overrides[get_session] = session_override
        with TestClient(app) as client:
            session_response = client.post(
                "/workout-sessions/",
                json={"workout_id": str(workout_id)},
            )
            self.assertEqual(session_response.status_code, 201)
            session_data = session_response.json()
            workout_session_id = session_data["id"]
            self.assertIsNotNone(session_data["date"])
            self.assertIsNone(session_data["ended_at"])
            self.assertEqual(session_data["workout_id"], str(workout_id))
            self.assertEqual(session_data["workout_name"], "API Workout")
            self.assertNotEqual(session_data["user_workout_id"], str(workout_id))

            payload = {
                "exercise_id": str(exercise_id),
                "reps": 8,
                "weight": 40,
            }
            first = client.post(
                f"/workout-sessions/{workout_session_id}/logs", json=payload
            )
            second = client.post(
                f"/workout-sessions/{workout_session_id}/logs", json=payload
            )
            self.assertEqual(first.status_code, 201)
            self.assertEqual(second.status_code, 201)
            first_log_id = first.json()["id"]
            second_log_id = second.json()["id"]
            self.assertNotEqual(first_log_id, second_log_id)
            self.assertEqual(first.json()["workout_session_id"], workout_session_id)
            self.assertEqual(first.json()["exercise_id"], str(exercise_id))
            self.assertIsNotNone(first.json()["timestamp"])

            updated = client.patch(
                f"/workout-sessions/{workout_session_id}/logs/{first_log_id}",
                json={"reps": 10},
            )
            self.assertEqual(updated.status_code, 200)
            self.assertEqual(updated.json()["reps"], 10)
            deleted = client.delete(
                f"/workout-sessions/{workout_session_id}/logs/{first_log_id}"
            )
            self.assertEqual(deleted.status_code, 204)

            logs = client.get(f"/workout-sessions/{workout_session_id}/logs")
            self.assertEqual(logs.status_code, 200)
            self.assertEqual([item["id"] for item in logs.json()], [second_log_id])

            end_response = client.post(
                f"/workout-sessions/{workout_session_id}/end"
            )
            self.assertEqual(end_response.status_code, 200)
            ended_at = end_response.json()["ended_at"]
            self.assertIsNotNone(ended_at)

            repeated_end = client.post(
                f"/workout-sessions/{workout_session_id}/end"
            )
            self.assertEqual(repeated_end.status_code, 200)
            self.assertEqual(repeated_end.json()["ended_at"], ended_at)

            rejected_log = client.post(
                f"/workout-sessions/{workout_session_id}/logs",
                json=payload,
            )
            self.assertEqual(rejected_log.status_code, 409)



if __name__ == "__main__":
    unittest.main()
