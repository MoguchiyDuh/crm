import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.redis import close_redis, get_redis
from app.routers import activity, attachments, auth, employees, meetings, projects, reference, search, stats, users, ws


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis-backed sliding-window rate limiter."""

    async def dispatch(self, request: Request, call_next):
        redis = await get_redis()
        ip = request.client.host if request.client else "unknown"

        if request.url.path == "/api/auth/login":
            key = f"rl:login:{ip}"
            limit, window = 10, 60
        else:
            key = f"rl:api:{ip}"
            limit, window = 300, 60

        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, window)
        if count > limit:
            return JSONResponse(
                {"detail": "Rate limit exceeded. Try again later."},
                status_code=429,
                headers={"Retry-After": str(window)},
            )
        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_redis()
    yield
    await close_redis()


app = FastAPI(
    title="CRM API",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(RateLimitMiddleware)
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
app.include_router(activity.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(attachments.router, prefix="/api")
app.include_router(ws.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
