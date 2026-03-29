from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.employee import EmployeeOut
from app.schemas.reference import ProjectPriorityOut, ProjectStatusOut


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    status_id: int
    priority_id: int
    manager_id: int | None = None
    start_date: datetime | None = None
    deadline_date: datetime | None = None
    budget: float | None = None
    spent_hours: int | None = None
    progress: int = Field(default=0, ge=0, le=100)
    client_name: str | None = None
    client_contact: str | None = None
    tags: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status_id: int | None = None
    priority_id: int | None = None
    manager_id: int | None = None
    start_date: datetime | None = None
    deadline_date: datetime | None = None
    actual_start_date: datetime | None = None
    actual_end_date: datetime | None = None
    budget: float | None = None
    spent_hours: int | None = None
    progress: int | None = Field(default=None, ge=0, le=100)
    client_name: str | None = None
    client_contact: str | None = None
    tags: str | None = None


class ProjectOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    description: str | None
    status: ProjectStatusOut
    priority: ProjectPriorityOut
    manager: EmployeeOut | None
    start_date: datetime | None
    deadline_date: datetime | None
    actual_start_date: datetime | None
    actual_end_date: datetime | None
    budget: float | None
    spent_hours: int | None
    progress: int
    client_name: str | None
    client_contact: str | None
    tags: str | None
    created_at: datetime
    updated_at: datetime


class ProjectFilters(BaseModel):
    status_id: int | None = None
    priority_id: int | None = None
    manager_id: int | None = None
    search: str | None = None
