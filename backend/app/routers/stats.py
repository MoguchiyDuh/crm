from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.deps import current_user, db_session
from app.models.employee import Employee
from app.models.meeting import Meeting
from app.models.project import Project
from app.models.reference import ProjectPriority, ProjectStatus
from app.models.user import User

router = APIRouter(prefix="/stats", tags=["stats"])


class StatusStat(BaseModel):
    status: str
    count: int


class PriorityStat(BaseModel):
    priority: str
    count: int
    color: str | None


class StatsOut(BaseModel):
    projects_total: int
    projects_by_status: list[StatusStat]
    projects_by_priority: list[PriorityStat]
    employees_active: int
    meetings_total: int
    meetings_upcoming: int
    projects_overdue: int


@router.get("", response_model=StatsOut)
async def get_stats(
    db: AsyncSession = Depends(db_session),
    _: User = Depends(current_user),
) -> StatsOut:
    now = datetime.now(timezone.utc)
    week_ahead = now + timedelta(days=7)

    # Counts
    projects_total = (await db.execute(select(func.count()).select_from(Project))).scalar_one()
    employees_active = (
        await db.execute(
            select(func.count()).select_from(Employee).where(Employee.is_active == True)  # noqa: E712
        )
    ).scalar_one()
    meetings_total = (await db.execute(select(func.count()).select_from(Meeting))).scalar_one()
    meetings_upcoming = (
        await db.execute(
            select(func.count())
            .select_from(Meeting)
            .where(Meeting.scheduled_at >= now, Meeting.scheduled_at <= week_ahead)
        )
    ).scalar_one()
    projects_overdue = (
        await db.execute(
            select(func.count())
            .select_from(Project)
            .join(ProjectStatus, Project.status_id == ProjectStatus.id)
            .where(
                Project.deadline_date < now,
                ProjectStatus.name.notin_(["Done", "Completed", "Cancelled"]),
            )
        )
    ).scalar_one()

    # By status
    status_rows = (
        await db.execute(
            select(ProjectStatus.name, func.count(Project.id))
            .join(Project, Project.status_id == ProjectStatus.id, isouter=True)
            .group_by(ProjectStatus.id, ProjectStatus.name)
            .order_by(ProjectStatus.id)
        )
    ).all()
    projects_by_status = [StatusStat(status=r[0], count=r[1]) for r in status_rows]

    # By priority
    priority_rows = (
        await db.execute(
            select(ProjectPriority.name, ProjectPriority.color, func.count(Project.id))
            .join(Project, Project.priority_id == ProjectPriority.id, isouter=True)
            .group_by(ProjectPriority.id, ProjectPriority.name, ProjectPriority.color)
            .order_by(ProjectPriority.order.nullslast())
        )
    ).all()
    projects_by_priority = [
        PriorityStat(priority=r[0], count=r[2], color=r[1]) for r in priority_rows
    ]

    return StatsOut(
        projects_total=projects_total,
        projects_by_status=projects_by_status,
        projects_by_priority=projects_by_priority,
        employees_active=employees_active,
        meetings_total=meetings_total,
        meetings_upcoming=meetings_upcoming,
        projects_overdue=projects_overdue,
    )
