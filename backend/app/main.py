from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.redis import close_redis, get_redis
from app.routers import auth, employees, meetings, projects, reference, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_redis()
    yield
    await close_redis()


app = FastAPI(
    title="CRM API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(reference.router, prefix="/api")
app.include_router(employees.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(meetings.router, prefix="/api")
app.include_router(users.router, prefix="/api")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
