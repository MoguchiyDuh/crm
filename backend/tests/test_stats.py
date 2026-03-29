import pytest

from app.models.reference import ProjectPriority, ProjectStatus


@pytest.fixture(autouse=True)
async def seed_reference(db):
    db.add(ProjectStatus(name="Active", is_default=True))
    db.add(ProjectStatus(name="Done", is_default=False))
    db.add(ProjectPriority(name="High", order=1, color="#ff0000"))
    db.add(ProjectPriority(name="Low", order=2, color="#00ff00"))
    await db.commit()


async def _ids(client):
    sid = (await client.get("/api/reference/statuses")).json()[0]["id"]
    sid2 = (await client.get("/api/reference/statuses")).json()[1]["id"]
    pid = (await client.get("/api/reference/priorities")).json()[0]["id"]
    return sid, sid2, pid


@pytest.mark.asyncio
async def test_stats_empty(auth_client):
    r = await auth_client.get("/api/stats")
    assert r.status_code == 200
    data = r.json()
    assert data["projects_total"] == 0
    assert data["employees_active"] == 0
    assert data["meetings_total"] == 0
    assert data["meetings_upcoming"] == 0
    assert data["projects_overdue"] == 0
    assert isinstance(data["projects_by_status"], list)
    assert isinstance(data["projects_by_priority"], list)


@pytest.mark.asyncio
async def test_stats_project_count(auth_client):
    sid, _, pid = await _ids(auth_client)
    await auth_client.post("/api/projects", json={"name": "P1", "status_id": sid, "priority_id": pid})
    await auth_client.post("/api/projects", json={"name": "P2", "status_id": sid, "priority_id": pid})

    r = await auth_client.get("/api/stats")
    assert r.json()["projects_total"] == 2


@pytest.mark.asyncio
async def test_stats_by_status_breakdown(auth_client):
    sid_active, sid_done, pid = await _ids(auth_client)
    await auth_client.post("/api/projects", json={"name": "P1", "status_id": sid_active, "priority_id": pid})
    await auth_client.post("/api/projects", json={"name": "P2", "status_id": sid_done, "priority_id": pid})

    r = await auth_client.get("/api/stats")
    by_status = {s["status"]: s["count"] for s in r.json()["projects_by_status"]}
    assert by_status["Active"] == 1
    assert by_status["Done"] == 1


@pytest.mark.asyncio
async def test_stats_by_priority_breakdown(auth_client):
    sid, _, pid_high = await _ids(auth_client)
    pid_low = (await auth_client.get("/api/reference/priorities")).json()[1]["id"]
    await auth_client.post("/api/projects", json={"name": "P1", "status_id": sid, "priority_id": pid_high})
    await auth_client.post("/api/projects", json={"name": "P2", "status_id": sid, "priority_id": pid_high})
    await auth_client.post("/api/projects", json={"name": "P3", "status_id": sid, "priority_id": pid_low})

    r = await auth_client.get("/api/stats")
    by_priority = {p["priority"]: p["count"] for p in r.json()["projects_by_priority"]}
    assert by_priority["High"] == 2
    assert by_priority["Low"] == 1


@pytest.mark.asyncio
async def test_stats_employee_count(auth_client):
    await auth_client.post("/api/employees", json={"full_name": "E1", "role": "Dev"})
    await auth_client.post("/api/employees", json={"full_name": "E2", "role": "QA"})

    r = await auth_client.get("/api/stats")
    assert r.json()["employees_active"] == 2


@pytest.mark.asyncio
async def test_stats_employee_soft_delete_excluded(auth_client):
    r = await auth_client.post("/api/employees", json={"full_name": "Gone", "role": "Dev"})
    emp_id = r.json()["id"]
    await auth_client.delete(f"/api/employees/{emp_id}")

    r2 = await auth_client.get("/api/stats")
    assert r2.json()["employees_active"] == 0


@pytest.mark.asyncio
async def test_stats_unauthenticated(client):
    r = await client.get("/api/stats")
    assert r.status_code == 401
