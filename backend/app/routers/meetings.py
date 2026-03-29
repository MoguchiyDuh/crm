from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.deps import current_user, db_session
from app.exceptions import Conflict, NotFound
from app.models.employee import Employee
from app.models.meeting import Meeting, MeetingParticipant
from app.models.project import Project
from app.models.user import User
from app.schemas.meeting import MeetingCreate, MeetingOut, MeetingUpdate

router = APIRouter(prefix="/meetings", tags=["meetings"])


async def _get_meeting_full(db: AsyncSession, meeting_id: int) -> Meeting | None:
    result = await db.execute(
        select(Meeting)
        .options(
            selectinload(Meeting.participants).selectinload(MeetingParticipant.employee)
        )
        .where(Meeting.id == meeting_id)
    )
    return result.scalar_one_or_none()


@router.get("", response_model=list[MeetingOut])
async def list_meetings(
    db: AsyncSession = Depends(db_session),
    _: User = Depends(current_user),
) -> list[Meeting]:
    result = await db.execute(
        select(Meeting)
        .options(
            selectinload(Meeting.participants).selectinload(MeetingParticipant.employee)
        )
        .order_by(Meeting.scheduled_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=MeetingOut, status_code=201)
async def create_meeting(
    body: MeetingCreate,
    db: AsyncSession = Depends(db_session),
    _: User = Depends(current_user),
) -> Meeting:
    project = await db.get(Project, body.project_id)
    if not project:
        raise NotFound("Project")

    meeting = Meeting(
        title=body.title,
        scheduled_at=body.scheduled_at,
        project_id=body.project_id,
        meeting_link=body.meeting_link,
        notes=body.notes,
    )
    db.add(meeting)
    await db.flush()

    for emp_id in body.participant_ids:
        emp = await db.get(Employee, emp_id)
        if emp:
            db.add(MeetingParticipant(meeting_id=meeting.id, employee_id=emp_id))

    await db.commit()
    return await _get_meeting_full(db, meeting.id)


@router.get("/{meeting_id}", response_model=MeetingOut)
async def get_meeting(
    meeting_id: int,
    db: AsyncSession = Depends(db_session),
    _: User = Depends(current_user),
) -> Meeting:
    meeting = await _get_meeting_full(db, meeting_id)
    if not meeting:
        raise NotFound("Meeting")
    return meeting


@router.patch("/{meeting_id}", response_model=MeetingOut)
async def update_meeting(
    meeting_id: int,
    body: MeetingUpdate,
    db: AsyncSession = Depends(db_session),
    _: User = Depends(current_user),
) -> Meeting:
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    meeting = result.scalar_one_or_none()
    if not meeting:
        raise NotFound("Meeting")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(meeting, field, value)

    await db.commit()
    return await _get_meeting_full(db, meeting_id)


@router.delete("/{meeting_id}", status_code=204)
async def delete_meeting(
    meeting_id: int,
    db: AsyncSession = Depends(db_session),
    _: User = Depends(current_user),
) -> None:
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    meeting = result.scalar_one_or_none()
    if not meeting:
        raise NotFound("Meeting")
    await db.delete(meeting)
    await db.commit()


@router.post("/{meeting_id}/participants/{employee_id}", response_model=MeetingOut)
async def add_participant(
    meeting_id: int,
    employee_id: int,
    db: AsyncSession = Depends(db_session),
    _: User = Depends(current_user),
) -> Meeting:
    meeting = await db.get(Meeting, meeting_id)
    if not meeting:
        raise NotFound("Meeting")
    employee = await db.get(Employee, employee_id)
    if not employee:
        raise NotFound("Employee")

    existing = await db.execute(
        select(MeetingParticipant).where(
            MeetingParticipant.meeting_id == meeting_id,
            MeetingParticipant.employee_id == employee_id,
        )
    )
    if existing.scalar_one_or_none():
        raise Conflict("Employee already a participant")

    db.add(MeetingParticipant(meeting_id=meeting_id, employee_id=employee_id))
    await db.commit()
    return await _get_meeting_full(db, meeting_id)


@router.delete("/{meeting_id}/participants/{employee_id}", status_code=204)
async def remove_participant(
    meeting_id: int,
    employee_id: int,
    db: AsyncSession = Depends(db_session),
    _: User = Depends(current_user),
) -> None:
    result = await db.execute(
        select(MeetingParticipant).where(
            MeetingParticipant.meeting_id == meeting_id,
            MeetingParticipant.employee_id == employee_id,
        )
    )
    participant = result.scalar_one_or_none()
    if not participant:
        raise NotFound("Participant")
    await db.delete(participant)
    await db.commit()
