from datetime import datetime

from pydantic import BaseModel

from app.schemas.employee import EmployeeOut


class MeetingCreate(BaseModel):
    title: str
    scheduled_at: datetime
    project_id: int
    meeting_link: str | None = None
    notes: str | None = None
    participant_ids: list[int] = []


class MeetingUpdate(BaseModel):
    title: str | None = None
    scheduled_at: datetime | None = None
    actual_at: datetime | None = None
    status: str | None = None
    meeting_link: str | None = None
    notes: str | None = None


class ParticipantOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    employee: EmployeeOut


class MeetingOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    title: str
    scheduled_at: datetime
    actual_at: datetime | None
    status: str
    meeting_link: str | None
    notes: str | None
    project_id: int
    created_at: datetime
    participants: list[ParticipantOut]
