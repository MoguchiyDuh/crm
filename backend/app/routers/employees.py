from fastapi import APIRouter, Depends
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import admin_user, current_user, db_session, redis_client
from app.exceptions import BadRequest, Conflict, NotFound
from app.models.employee import Employee
from app.models.user import User
from app.schemas.employee import EmployeeCreate, EmployeeOut, EmployeeUpdate
from app.services.activity import log_activity
from app.services.ws import manager
from app.services.cache import EMPLOYEES_KEY, EMPLOYEES_TTL, cached, invalidate

router = APIRouter(prefix="/employees", tags=["employees"])


async def _load_employees(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(Employee).where(Employee.is_active == True))  # noqa: E712
    rows = result.scalars().all()
    return [EmployeeOut.model_validate(r).model_dump() for r in rows]


@router.get("", response_model=list[EmployeeOut])
async def list_employees(
    db: AsyncSession = Depends(db_session),
    redis: Redis = Depends(redis_client),
    _: User = Depends(current_user),
) -> list[EmployeeOut]:
    data = await cached(redis, EMPLOYEES_KEY, EMPLOYEES_TTL, lambda: _load_employees(db))
    return [EmployeeOut(**item) for item in data]


@router.post("", response_model=EmployeeOut, status_code=201)
async def create_employee(
    body: EmployeeCreate,
    db: AsyncSession = Depends(db_session),
    redis: Redis = Depends(redis_client),
    me: User = Depends(current_user),
) -> Employee:
    employee = Employee(**body.model_dump())
    db.add(employee)
    await db.flush()
    await log_activity(db, me.id, "created", "employee", employee.id, employee.full_name)
    await db.commit()
    await db.refresh(employee)
    await invalidate(redis, EMPLOYEES_KEY)
    await manager.broadcast("employee.created", id=employee.id)
    return employee


@router.get("/{employee_id}", response_model=EmployeeOut)
async def get_employee(
    employee_id: int,
    db: AsyncSession = Depends(db_session),
    _: User = Depends(current_user),
) -> Employee:
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFound("Employee")
    return employee


@router.patch("/{employee_id}", response_model=EmployeeOut)
async def update_employee(
    employee_id: int,
    body: EmployeeUpdate,
    db: AsyncSession = Depends(db_session),
    redis: Redis = Depends(redis_client),
    me: User = Depends(current_user),
) -> Employee:
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFound("Employee")

    changed = body.model_dump(exclude_unset=True)
    for field, value in changed.items():
        setattr(employee, field, value)

    await log_activity(db, me.id, "updated", "employee", employee.id, employee.full_name, changed)
    await db.commit()
    await db.refresh(employee)
    await invalidate(redis, EMPLOYEES_KEY)
    await manager.broadcast("employee.updated", id=employee_id)
    return employee


@router.delete("/{employee_id}", status_code=204)
async def delete_employee(
    employee_id: int,
    db: AsyncSession = Depends(db_session),
    redis: Redis = Depends(redis_client),
    me: User = Depends(current_user),
) -> None:
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFound("Employee")

    await log_activity(db, me.id, "deleted", "employee", employee.id, employee.full_name)
    employee.is_active = False
    await db.commit()
    await invalidate(redis, EMPLOYEES_KEY)
    await manager.broadcast("employee.deleted", id=employee_id)


class LinkUserBody(BaseModel):
    user_id: int


@router.post("/{employee_id}/link", response_model=EmployeeOut)
async def link_user(
    employee_id: int,
    body: LinkUserBody,
    db: AsyncSession = Depends(db_session),
    redis: Redis = Depends(redis_client),
    me: User = Depends(admin_user),
) -> Employee:
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFound("Employee")

    target_user = await db.get(User, body.user_id)
    if not target_user:
        raise NotFound("User")

    # Check user not already linked to another employee
    existing = await db.execute(
        select(Employee).where(Employee.user_id == body.user_id, Employee.id != employee_id)
    )
    if existing.scalar_one_or_none():
        raise Conflict("User already linked to another employee")

    employee.user_id = body.user_id
    await log_activity(
        db, me.id, "linked", "employee", employee.id, employee.full_name,
        {"user_id": body.user_id, "user_email": target_user.email}
    )
    await db.commit()
    await db.refresh(employee)
    await invalidate(redis, EMPLOYEES_KEY)
    await manager.broadcast("employee.updated", id=employee_id)
    return employee


@router.delete("/{employee_id}/link", response_model=EmployeeOut)
async def unlink_user(
    employee_id: int,
    db: AsyncSession = Depends(db_session),
    redis: Redis = Depends(redis_client),
    me: User = Depends(admin_user),
) -> Employee:
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFound("Employee")
    if employee.user_id is None:
        raise BadRequest("Employee has no linked user")

    await log_activity(db, me.id, "unlinked", "employee", employee.id, employee.full_name)
    employee.user_id = None
    await db.commit()
    await db.refresh(employee)
    await invalidate(redis, EMPLOYEES_KEY)
    await manager.broadcast("employee.updated", id=employee_id)
    return employee
