import pytest

from app.models.reference import ProjectPriority, ProjectStatus


@pytest.fixture(autouse=True)
async def seed_reference(db):
    db.add(ProjectStatus(name="Active", is_default=True))
    db.add(ProjectPriority(name="High", order=1))
    await db.commit()


async def _make_project(auth_client):
    sr = await auth_client.get("/api/reference/statuses")
    pr = await auth_client.get("/api/reference/priorities")
    sid = sr.json()[0]["id"]
    pid = pr.json()[0]["id"]
    r = await auth_client.post("/api/projects", json={"name": "MeetingProject", "status_id": sid, "priority_id": pid})
    return r.json()["id"]


async def _make_employee(auth_client):
    r = await auth_client.post("/api/employees", json={"full_name": "Bob", "role": "Dev"})
    return r.json()["id"]


@pytest.mark.asyncio
async def test_list_meetings_empty(auth_client):
    r = await auth_client.get("/api/meetings")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_create_meeting(auth_client):
    proj_id = await _make_project(auth_client)
    r = await auth_client.post("/api/meetings", json={
        "title": "Sprint Review",
        "scheduled_at": "2025-06-01T10:00:00",
        "project_id": proj_id,
    })
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "Sprint Review"
    assert data["project_id"] == proj_id
    assert data["status"] == "planned"


@pytest.mark.asyncio
async def test_create_meeting_with_participants(auth_client):
    proj_id = await _make_project(auth_client)
    emp_id = await _make_employee(auth_client)
    r = await auth_client.post("/api/meetings", json={
        "title": "Kickoff",
        "scheduled_at": "2025-06-02T09:00:00",
        "project_id": proj_id,
        "participant_ids": [emp_id],
    })
    assert r.status_code == 201
    participants = r.json()["participants"]
    assert len(participants) == 1
    assert participants[0]["employee"]["id"] == emp_id


@pytest.mark.asyncio
async def test_add_participant(auth_client):
    proj_id = await _make_project(auth_client)
    emp_id = await _make_employee(auth_client)
    r = await auth_client.post("/api/meetings", json={
        "title": "Demo", "scheduled_at": "2025-07-01T15:00:00", "project_id": proj_id,
    })
    meeting_id = r.json()["id"]
    r2 = await auth_client.post(f"/api/meetings/{meeting_id}/participants/{emp_id}")
    assert r2.status_code == 200
    assert len(r2.json()["participants"]) == 1


@pytest.mark.asyncio
async def test_add_duplicate_participant(auth_client):
    proj_id = await _make_project(auth_client)
    emp_id = await _make_employee(auth_client)
    r = await auth_client.post("/api/meetings", json={
        "title": "Demo2", "scheduled_at": "2025-07-02T15:00:00",
        "project_id": proj_id, "participant_ids": [emp_id],
    })
    meeting_id = r.json()["id"]
    r2 = await auth_client.post(f"/api/meetings/{meeting_id}/participants/{emp_id}")
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_remove_participant(auth_client):
    proj_id = await _make_project(auth_client)
    emp_id = await _make_employee(auth_client)
    r = await auth_client.post("/api/meetings", json={
        "title": "Retro", "scheduled_at": "2025-08-01T11:00:00",
        "project_id": proj_id, "participant_ids": [emp_id],
    })
    meeting_id = r.json()["id"]
    r2 = await auth_client.delete(f"/api/meetings/{meeting_id}/participants/{emp_id}")
    assert r2.status_code == 204


@pytest.mark.asyncio
async def test_delete_meeting(auth_client):
    proj_id = await _make_project(auth_client)
    r = await auth_client.post("/api/meetings", json={
        "title": "ToDelete", "scheduled_at": "2025-09-01T10:00:00", "project_id": proj_id,
    })
    meeting_id = r.json()["id"]
    r2 = await auth_client.delete(f"/api/meetings/{meeting_id}")
    assert r2.status_code == 204
    r3 = await auth_client.get(f"/api/meetings/{meeting_id}")
    assert r3.status_code == 404
