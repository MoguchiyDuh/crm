from datetime import datetime

from pydantic import BaseModel


class AttachmentOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    entity_type: str
    entity_id: int
    filename: str
    mime_type: str
    size: int
    uploaded_by_id: int | None
    created_at: datetime
