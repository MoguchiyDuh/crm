from datetime import datetime

from pydantic import BaseModel


class ActivityLogOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    user_id: int | None
    user_email: str | None = None
    action: str
    entity_type: str
    entity_id: int | None
    entity_name: str | None
    details: str | None
    created_at: datetime

    @classmethod
    def from_orm_with_user(cls, log: object) -> "ActivityLogOut":
        return cls(
            id=log.id,  # type: ignore[attr-defined]
            user_id=log.user_id,  # type: ignore[attr-defined]
            user_email=log.user.email if log.user else None,  # type: ignore[attr-defined]
            action=log.action,  # type: ignore[attr-defined]
            entity_type=log.entity_type,  # type: ignore[attr-defined]
            entity_id=log.entity_id,  # type: ignore[attr-defined]
            entity_name=log.entity_name,  # type: ignore[attr-defined]
            details=log.details,  # type: ignore[attr-defined]
            created_at=log.created_at,  # type: ignore[attr-defined]
        )
