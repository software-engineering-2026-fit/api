# api
FastAPI backend

## Run with Docker

Requirements: Docker Desktop with Docker Compose.

1. From the project directory, create the environment file:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Edit `.env` and replace `POSTGRES_PASSWORD` and `SECRET_KEY` with your own
   values. Keep `POSTGRES_USER` and `POSTGRES_DB` consistent with the values
   configured there.

3. Build and start the API and database:

   ```powershell
   docker compose up --build -d
   ```

   The API waits for the database to become healthy and applies database
   migrations automatically when it starts.

4. Open the API documentation at <http://localhost:8000/docs>. Check
   <http://localhost:8000/health> for the health endpoint. To follow the API
   startup logs, run:

   ```powershell
   docker compose logs -f api
   ```

To open a PostgreSQL prompt in the database container:

```powershell
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

Stop the containers with `docker compose down`. The database volume is kept,
so its data remains for the next start.

## Authentication

The API uses OAuth2 password flow with bearer JWT access tokens.

Set `SECRET_KEY` in the environment before starting the API. Copy
`.env.example` to `.env` for local configuration and replace the example
secret with a long random value.

1. Register with `POST /auth/register`:

   ```json
   {
     "email": "user@example.com",
     "name": "Example User",
     "password": "a-strong-password"
   }
   ```

2. Request a token from `POST /auth/token` using form fields:
   `username` (the user's email) and `password`.

3. Send the returned token as `Authorization: Bearer <token>`.

The `/users` and `/workouts` endpoints require authentication. `/auth/me`
returns the authenticated user.

## Workout sessions and exercise logs

Create a workout, then add each exercise with `POST /workouts/{workout_id}/exercises`.
Each entry requires an exercise ID and may include a workout-specific
description.

Create a session with `POST /workout-sessions` using a workout UUID accessible
to the current user and a datetime:

```json
{
  "workout_id": "00000000-0000-0000-0000-000000000000",
  "date": "2026-11-13T09:00:00Z"
}
```

Add each performed set independently with
`POST /workout-sessions/{session_id}/logs`, for example:

```json
{
  "exercise_id": "00000000-0000-0000-0000-000000000000",
  "reps": 8,
  "weight": 40,
  "exhaustion_level": 4
}
```

Individual set logs can be updated with `PATCH` or removed with `DELETE` at
`/workout-sessions/{session_id}/logs/{log_id}`. A session can contain multiple
logs for the same exercise. Finish a session with
`POST /workout-sessions/{session_id}/end`; the response includes `ended_at`.
Ending is idempotent, and new logs are rejected once a session has ended.

The `20261113_0011` migration retains existing memberships and workout log
history, converts each legacy set count into separate UUID-backed records, and
retains old planned set/repetition/weight values in the workout-exercise
association description. The former log tables are removed after migration.
Downgrading this migration is unsupported because the new per-set logs cannot
always be represented by the old composite-key log schema.

Database migrations are managed with Alembic:

```shell
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "describe the schema change"
```

The Docker entrypoint runs `alembic upgrade head` before starting the API.
The initial migration also adds `users.hashed_password` for databases created
before authentication was added. Existing users receive an empty password hash
and cannot log in until a password-reset flow is implemented.

User and workout identifiers use UUIDs. The UUID migration preserves existing
rows by assigning each existing user and workout a new UUID and updating the
workout foreign keys. Existing access tokens must be issued again after this
migration because their user ID subjects used the previous identifier format.
