import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import ActivityLog


async def log_activity(
    db: AsyncSession,
    user_id: int | None,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    entity_name: str | None = None,
    details: dict | None = None,
) -> None:
    """Fire-and-persist activity log entry."""
    log = ActivityLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name,
        details=json.dumps(details) if details else None,
    )
    db.add(log)
    # Flushed on commit in caller; caller must commit after this.
