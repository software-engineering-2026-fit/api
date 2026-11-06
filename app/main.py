from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.auth import router as auth_router
from app.routes.exercises import router as exercises_router
from app.routes.users import router as users_router
from app.routes.workouts import router as workouts_router
from app.routes.workout_logs import router as workout_logs_router


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)
app.include_router(workouts_router)
app.include_router(workout_logs_router)
app.include_router(auth_router)
app.include_router(exercises_router)


@app.get("/")
async def root():
    return {"message": "Hello World!!!!"}

@app.get("/health")
def health():
    return {"status": "ok"}
