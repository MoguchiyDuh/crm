from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.deps import current_user, db_session
from app.exceptions import NotFound
from app.models.meeting import Meeting
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectFilters, ProjectOut, ProjectUpdate
from app.services.activity import log_activity
from app.services.ws import manager

router = APIRouter(prefix="/projects", tags=["projects"])


def _apply_filters(stmt, filters: ProjectFilters):
    if filters.status_id is not None:
        stmt = stmt.where(Project.status_id == filters.status_id)
    if filters.priority_id is not None:
        stmt = stmt.where(Project.priority_id == filters.priority_id)
    if filters.manager_id is not None:
        stmt = stmt.where(Project.manager_id == filters.manager_id)
    if filters.search:
        term = f"%{filters.search}%"
        stmt = stmt.where(
            or_(
                Project.name.ilike(term),
                Project.description.ilike(term),
                Project.client_name.ilike(term),
            )
        )
    return stmt


@router.get("", response_model=list[ProjectOut])
async def list_projects(
    status_id: int | None = Query(None),
    priority_id: int | None = Query(None),
    manager_id: int | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(db_session),
    _: User = Depends(current_user),
) -> list[Project]:
    filters = ProjectFilters(
        status_id=status_id,
        priority_id=priority_id,
        manager_id=manager_id,
        search=search,
    )
    stmt = (
        select(Project)
        .options(
            selectinload(Project.status),
            selectinload(Project.priority),
            selectinload(Project.manager),
        )
        .order_by(Project.created_at.desc())
    )
    stmt = _apply_filters(stmt, filters)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=ProjectOut, status_code=201)
async def create_project(
    body: ProjectCreate,
    db: AsyncSession = Depends(db_session),
    me: User = Depends(current_user),
) -> Project:
    project = Project(**body.model_dump())
    db.add(project)
    await db.flush()
    await log_activity(db, me.id, "created", "project", project.id, project.name)
    await db.commit()
    await manager.broadcast("project.created", id=project.id)

    result = await db.execute(
        select(Project)
        .options(
            selectinload(Project.status),
            selectinload(Project.priority),
            selectinload(Project.manager),
        )
        .where(Project.id == project.id)
    )
    return result.scalar_one()


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(db_session),
    _: User = Depends(current_user),
) -> Project:
    result = await db.execute(
        select(Project)
        .options(
            selectinload(Project.status),
            selectinload(Project.priority),
            selectinload(Project.manager),
        )
        .where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise NotFound("Project")
    return project


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: int,
    body: ProjectUpdate,
    db: AsyncSession = Depends(db_session),
    me: User = Depends(current_user),
) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise NotFound("Project")

    changed = body.model_dump(exclude_unset=True)
    for field, value in changed.items():
        setattr(project, field, value)

    await log_activity(db, me.id, "updated", "project", project.id, project.name, changed)
    await db.commit()
    await manager.broadcast("project.updated", id=project_id)

    result = await db.execute(
        select(Project)
        .options(
            selectinload(Project.status),
            selectinload(Project.priority),
            selectinload(Project.manager),
        )
        .where(Project.id == project_id)
    )
    return result.scalar_one()


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(db_session),
    me: User = Depends(current_user),
) -> None:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise NotFound("Project")

    await log_activity(db, me.id, "deleted", "project", project.id, project.name)
    await db.delete(project)
    await db.commit()
    await manager.broadcast("project.deleted", id=project_id)
