import json

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import admin_user, db_session, redis_client
from app.models.reference import ProjectPriority, ProjectStatus
from app.models.user import User
from app.schemas.reference import (
    ProjectPriorityCreate,
    ProjectPriorityOut,
    ProjectStatusCreate,
    ProjectStatusOut,
)
from app.services.cache import PRIORITIES_KEY, REF_TTL, STATUSES_KEY, cached, invalidate

router = APIRouter(prefix="/reference", tags=["reference"])


@router.get("/statuses", response_model=list[ProjectStatusOut])
async def get_statuses(
    db: AsyncSession = Depends(db_session),
    redis: Redis = Depends(redis_client),
) -> list[ProjectStatusOut]:
    async def load():
        result = await db.execute(select(ProjectStatus))
        rows = result.scalars().all()
        return [ProjectStatusOut.model_validate(r).model_dump() for r in rows]

    data = await cached(redis, STATUSES_KEY, REF_TTL, load)
    return [ProjectStatusOut(**item) for item in data]


@router.post("/statuses", response_model=ProjectStatusOut, status_code=201)
async def create_status(
    body: ProjectStatusCreate,
    db: AsyncSession = Depends(db_session),
    redis: Redis = Depends(redis_client),
    _: User = Depends(admin_user),
) -> ProjectStatus:
    status = ProjectStatus(**body.model_dump())
    db.add(status)
    await db.commit()
    await db.refresh(status)
    await invalidate(redis, STATUSES_KEY)
    return status


@router.get("/priorities", response_model=list[ProjectPriorityOut])
async def get_priorities(
    db: AsyncSession = Depends(db_session),
    redis: Redis = Depends(redis_client),
) -> list[ProjectPriorityOut]:
    async def load():
        result = await db.execute(select(ProjectPriority).order_by(ProjectPriority.order))
        rows = result.scalars().all()
        return [ProjectPriorityOut.model_validate(r).model_dump() for r in rows]

    data = await cached(redis, PRIORITIES_KEY, REF_TTL, load)
    return [ProjectPriorityOut(**item) for item in data]


@router.post("/priorities", response_model=ProjectPriorityOut, status_code=201)
async def create_priority(
    body: ProjectPriorityCreate,
    db: AsyncSession = Depends(db_session),
    redis: Redis = Depends(redis_client),
    _: User = Depends(admin_user),
) -> ProjectPriority:
    priority = ProjectPriority(**body.model_dump())
    db.add(priority)
    await db.commit()
    await db.refresh(priority)
    await invalidate(redis, PRIORITIES_KEY)
    return priority
