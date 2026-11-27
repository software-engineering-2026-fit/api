# API

FastAPI backend for managing users, exercise catalog entries, workouts,
workout sessions, and individual set logs. The API uses SQLModel/Alembic,
PostgreSQL in Docker, SQLite for the default local configuration, and OAuth2
bearer JWT authentication.

## Requirements

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/) for local Python and dependency management
- Docker Desktop with Docker Compose for the recommended setup

## Run with Docker

1. Create the environment file:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Replace `POSTGRES_PASSWORD` and `SECRET_KEY` in `.env` with secure values.
   Keep `POSTGRES_USER` and `POSTGRES_DB` consistent between the PostgreSQL
   container and your local configuration.

3. Build and start the API and database:

   ```powershell
   docker compose up --build -d
   ```

   Compose waits for PostgreSQL to become healthy, and the API container runs
   `alembic upgrade head` before starting Uvicorn.

4. Open <http://localhost:8000/docs> for Swagger UI or
   <http://localhost:8000/redoc> for ReDoc. Check
   <http://localhost:8000/health> for the health endpoint.

Follow API logs or open a PostgreSQL prompt with:

```powershell
docker compose logs -f api
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

Stop the containers with `docker compose down`. The `postgres_data` volume is
kept, so database data remains for the next start.

## Local development

Install the locked dependencies and start a local server:

```powershell
uv sync --frozen
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

Without `DATABASE_URL`, the application uses `sqlite:///./app.db`. Set
`SECRET_KEY` before requesting or validating JWT tokens. For example:

```powershell
$env:DATABASE_URL = "sqlite:///./app.db"
$env:SECRET_KEY = "use-a-long-random-development-secret"
uv run uvicorn app.main:app --reload
```

Run the test suite with:

```powershell
uv run python -m unittest tests/test_workout_schema.py
```

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./app.db` | SQLAlchemy database URL. Docker Compose constructs a PostgreSQL URL from `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB`. |
| `POSTGRES_USER` | none in Compose | PostgreSQL role and database user. |
| `POSTGRES_PASSWORD` | none in Compose | PostgreSQL password. Change the example value in `.env`. |
| `POSTGRES_DB` | none in Compose | PostgreSQL database name. |
| `SECRET_KEY` | none | Required secret used to sign and verify JWT access tokens. |
| `JWT_ALGORITHM` | `HS256` | JWT signing and verification algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access-token lifetime in minutes. |

`DATABASE_URL` is optional for local SQLite development. In Docker, Compose
overrides it with a PostgreSQL connection to the `db` service.

`SECRET_KEY` must remain the same across API restarts and replicas that share
tokens. The password token flow is `/auth/token`; use the user's email as the
`username` form field.

## API overview

The API exposes these route groups:

- `/auth` - register, obtain a bearer token, and read the current user
- `/users` - list/read users and update the current user's name
- `/exercises` - list/filter/create the shared exercise catalog
- `/workouts` - create/list workouts and manage their exercises
- `/workout-sessions` - start/end/delete sessions and manage individual set logs
- `/health` - lightweight liveness response

All exercise access, user and workout operations, and workout sessions require
a bearer token. Workout access is limited to users who have a workout
membership.

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

The `/users`, `/exercises`, `/workouts`, `/workout-sessions`, and `/auth/me`
endpoints require authentication.

## Workout sessions and exercise logs

Create a workout, then add each exercise with `POST /workouts/{workout_id}/exercises`.
Each entry requires an exercise ID and may include a workout-specific
description.

Create a session with `POST /workout-sessions` using a workout UUID accessible
to the current user. `date` is optional and defaults to the current UTC time:

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
Session responses include `user_workout_id` for the user's membership and
`workout_id`/`workout_name` for the actual workout plan. Ending is idempotent,
and new logs are rejected once a session has ended.

The `20261113_0011` migration retains existing memberships and workout log
history, converts each legacy set count into separate UUID-backed records, and
retains old planned set/repetition/weight values in the workout-exercise
association description. The former log tables are removed after migration.
Migration `20261113_0012` adds nullable `ended_at` timestamps for workout
sessions and is applied by the Docker entrypoint and normal upgrade command.
Migration `20261127_0013` removes the workout `public` column. Workout access
is now granted only through user-workout memberships.
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
