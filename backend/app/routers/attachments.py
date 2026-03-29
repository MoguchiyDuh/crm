import mimetypes
import uuid
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import current_user, db_session
from app.exceptions import NotFound
from app.models.attachment import Attachment
from app.models.project import Project
from app.models.user import User
from app.schemas.attachment import AttachmentOut

router = APIRouter(tags=["attachments"])

UPLOADS_DIR = Path("/app/uploads")
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


def _uploads_path(entity_type: str, entity_id: int) -> Path:
    p = UPLOADS_DIR / entity_type / str(entity_id)
    p.mkdir(parents=True, exist_ok=True)
    return p


@router.get("/projects/{project_id}/attachments", response_model=list[AttachmentOut])
async def list_attachments(
    project_id: int,
    db: AsyncSession = Depends(db_session),
    _: User = Depends(current_user),
) -> list[Attachment]:
    project = await db.get(Project, project_id)
    if not project:
        raise NotFound("Project")
    result = await db.execute(
        select(Attachment)
        .where(Attachment.entity_type == "project", Attachment.entity_id == project_id)
        .order_by(Attachment.created_at.desc())
    )
    return result.scalars().all()


@router.post("/projects/{project_id}/attachments", response_model=AttachmentOut, status_code=201)
async def upload_attachment(
    project_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(db_session),
    me: User = Depends(current_user),
) -> Attachment:
    project = await db.get(Project, project_id)
    if not project:
        raise NotFound("Project")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds 50 MB limit")

    ext = Path(file.filename or "file").suffix
    stored_name = f"{uuid.uuid4().hex}{ext}"
    dest = _uploads_path("project", project_id) / stored_name

    async with aiofiles.open(dest, "wb") as f:
        await f.write(content)

    mime = file.content_type or mimetypes.guess_type(file.filename or "")[0] or "application/octet-stream"
    attachment = Attachment(
        entity_type="project",
        entity_id=project_id,
        filename=file.filename or stored_name,
        stored_name=stored_name,
        mime_type=mime,
        size=len(content),
        uploaded_by_id=me.id,
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)
    return attachment


@router.get("/attachments/{attachment_id}/download")
async def download_attachment(
    attachment_id: int,
    db: AsyncSession = Depends(db_session),
    _: User = Depends(current_user),
) -> FileResponse:
    attachment = await db.get(Attachment, attachment_id)
    if not attachment:
        raise NotFound("Attachment")

    path = _uploads_path(attachment.entity_type, attachment.entity_id) / attachment.stored_name
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=str(path),
        filename=attachment.filename,
        media_type=attachment.mime_type,
    )


@router.delete("/attachments/{attachment_id}", status_code=204)
async def delete_attachment(
    attachment_id: int,
    db: AsyncSession = Depends(db_session),
    _: User = Depends(current_user),
) -> None:
    attachment = await db.get(Attachment, attachment_id)
    if not attachment:
        raise NotFound("Attachment")

    path = _uploads_path(attachment.entity_type, attachment.entity_id) / attachment.stored_name
    if path.exists():
        path.unlink()

    await db.delete(attachment)
    await db.commit()
