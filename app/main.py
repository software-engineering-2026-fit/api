from fastapi import FastAPI

from app.routes.auth import router as auth_router
from app.routes.exercises import router as exercises_router
from app.routes.users import router as users_router
from app.routes.workouts import router as workouts_router


app = FastAPI()

app.include_router(users_router)
app.include_router(workouts_router)
app.include_router(auth_router)
app.include_router(exercises_router)


@app.get("/")
async def root():
    return {"message": "Hello World!!!!"}

@app.get("/health")
def health():
    return {"status": "ok"}
