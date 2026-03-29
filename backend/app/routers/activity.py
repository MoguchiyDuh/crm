from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.deps import current_user, db_session
from app.models.activity import ActivityLog
from app.models.user import User
from app.schemas.activity import ActivityLogOut

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("", response_model=list[ActivityLogOut])
async def list_activity(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    entity_type: str | None = Query(None),
    db: AsyncSession = Depends(db_session),
    me: User = Depends(current_user),
) -> list[ActivityLogOut]:
    stmt = (
        select(ActivityLog)
        .options(selectinload(ActivityLog.user))
        .order_by(ActivityLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if me.role != "admin":
        stmt = stmt.where(ActivityLog.user_id == me.id)
    if entity_type:
        stmt = stmt.where(ActivityLog.entity_type == entity_type)

    result = await db.execute(stmt)
    logs = result.scalars().all()
    return [ActivityLogOut.from_orm_with_user(log) for log in logs]
