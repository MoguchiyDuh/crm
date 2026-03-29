import io

import pytest

import app.routers.attachments as att_mod
from app.models.reference import ProjectPriority, ProjectStatus


@pytest.fixture(autouse=True)
async def seed_reference(db):
    db.add(ProjectStatus(name="Active", is_default=True))
    db.add(ProjectPriority(name="High", order=1))
    await db.commit()


@pytest.fixture(autouse=True)
def patch_uploads(tmp_path, monkeypatch):
    monkeypatch.setattr(att_mod, "UPLOADS_DIR", tmp_path)


async def _make_project(client):
    sid = (await client.get("/api/reference/statuses")).json()[0]["id"]
    pid = (await client.get("/api/reference/priorities")).json()[0]["id"]
    r = await client.post("/api/projects", json={"name": "Attach Test", "status_id": sid, "priority_id": pid})
    assert r.status_code == 201
    return r.json()["id"]


@pytest.mark.asyncio
async def test_list_attachments_empty(auth_client):
    proj_id = await _make_project(auth_client)
    r = await auth_client.get(f"/api/projects/{proj_id}/attachments")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_upload_attachment(auth_client):
    proj_id = await _make_project(auth_client)
    content = b"hello attachment"
    r = await auth_client.post(
        f"/api/projects/{proj_id}/attachments",
        files={"file": ("hello.txt", io.BytesIO(content), "text/plain")},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["filename"] == "hello.txt"
    assert data["mime_type"] == "text/plain"
    assert data["size"] == len(content)
    assert data["entity_id"] == proj_id


@pytest.mark.asyncio
async def test_upload_appears_in_list(auth_client):
    proj_id = await _make_project(auth_client)
    await auth_client.post(
        f"/api/projects/{proj_id}/attachments",
        files={"file": ("doc.pdf", io.BytesIO(b"pdf content"), "application/pdf")},
    )
    r = await auth_client.get(f"/api/projects/{proj_id}/attachments")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["filename"] == "doc.pdf"


@pytest.mark.asyncio
async def test_download_attachment(auth_client):
    proj_id = await _make_project(auth_client)
    content = b"download me"
    upload = await auth_client.post(
        f"/api/projects/{proj_id}/attachments",
        files={"file": ("data.bin", io.BytesIO(content), "application/octet-stream")},
    )
    att_id = upload.json()["id"]
    r = await auth_client.get(f"/api/attachments/{att_id}/download")
    assert r.status_code == 200
    assert r.content == content


@pytest.mark.asyncio
async def test_delete_attachment(auth_client):
    proj_id = await _make_project(auth_client)
    upload = await auth_client.post(
        f"/api/projects/{proj_id}/attachments",
        files={"file": ("bye.txt", io.BytesIO(b"bye"), "text/plain")},
    )
    att_id = upload.json()["id"]
    r = await auth_client.delete(f"/api/attachments/{att_id}")
    assert r.status_code == 204
    r2 = await auth_client.get(f"/api/projects/{proj_id}/attachments")
    assert r2.json() == []


@pytest.mark.asyncio
async def test_attachment_project_not_found(auth_client):
    r = await auth_client.get("/api/projects/99999/attachments")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_attachment_not_found(auth_client):
    r = await auth_client.get("/api/attachments/99999/download")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_attachment_unauthenticated(client):
    r = await client.get("/api/projects/1/attachments")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_multiple_attachments_same_project(auth_client):
    proj_id = await _make_project(auth_client)
    for i in range(3):
        await auth_client.post(
            f"/api/projects/{proj_id}/attachments",
            files={"file": (f"file{i}.txt", io.BytesIO(f"content {i}".encode()), "text/plain")},
        )
    r = await auth_client.get(f"/api/projects/{proj_id}/attachments")
    assert len(r.json()) == 3
