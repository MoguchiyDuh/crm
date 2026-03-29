import pytest

from app.models.reference import ProjectPriority, ProjectStatus


@pytest.fixture(autouse=True)
async def seed_reference(db):
    db.add(ProjectStatus(name="Active", is_default=True))
    db.add(ProjectStatus(name="Done"))
    db.add(ProjectPriority(name="High", order=1))
    db.add(ProjectPriority(name="Low", order=2))
    await db.commit()


async def _status_id(auth_client, name="Active"):
    r = await auth_client.get("/api/reference/statuses")
    return next(s["id"] for s in r.json() if s["name"] == name)


async def _priority_id(auth_client, name="High"):
    r = await auth_client.get("/api/reference/priorities")
    return next(p["id"] for p in r.json() if p["name"] == name)


@pytest.mark.asyncio
async def test_list_projects_empty(auth_client):
    r = await auth_client.get("/api/projects")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_create_project(auth_client):
    sid = await _status_id(auth_client)
    pid = await _priority_id(auth_client)
    r = await auth_client.post("/api/projects", json={
        "name": "Test Project",
        "status_id": sid,
        "priority_id": pid,
        "progress": 0,
    })
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Test Project"
    assert data["status"]["name"] == "Active"
    assert data["priority"]["name"] == "High"


@pytest.mark.asyncio
async def test_create_project_missing_fields(auth_client):
    r = await auth_client.post("/api/projects", json={"name": "No IDs"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_get_project(auth_client):
    sid = await _status_id(auth_client)
    pid = await _priority_id(auth_client)
    r = await auth_client.post("/api/projects", json={"name": "Proj X", "status_id": sid, "priority_id": pid})
    proj_id = r.json()["id"]
    r2 = await auth_client.get(f"/api/projects/{proj_id}")
    assert r2.status_code == 200
    assert r2.json()["id"] == proj_id


@pytest.mark.asyncio
async def test_update_project(auth_client):
    sid = await _status_id(auth_client)
    pid = await _priority_id(auth_client)
    r = await auth_client.post("/api/projects", json={"name": "Old", "status_id": sid, "priority_id": pid})
    proj_id = r.json()["id"]
    r2 = await auth_client.patch(f"/api/projects/{proj_id}", json={"name": "New", "progress": 50})
    assert r2.status_code == 200
    assert r2.json()["name"] == "New"
    assert r2.json()["progress"] == 50


@pytest.mark.asyncio
async def test_delete_project(auth_client):
    sid = await _status_id(auth_client)
    pid = await _priority_id(auth_client)
    r = await auth_client.post("/api/projects", json={"name": "ToDelete", "status_id": sid, "priority_id": pid})
    proj_id = r.json()["id"]
    r2 = await auth_client.delete(f"/api/projects/{proj_id}")
    assert r2.status_code == 204
    r3 = await auth_client.get(f"/api/projects/{proj_id}")
    assert r3.status_code == 404


@pytest.mark.asyncio
async def test_filter_by_status(auth_client):
    sid_active = await _status_id(auth_client, "Active")
    sid_done = await _status_id(auth_client, "Done")
    pid = await _priority_id(auth_client)
    await auth_client.post("/api/projects", json={"name": "P1", "status_id": sid_active, "priority_id": pid})
    await auth_client.post("/api/projects", json={"name": "P2", "status_id": sid_done, "priority_id": pid})
    r = await auth_client.get("/api/projects", params={"status_id": sid_done})
    assert r.status_code == 200
    names = [p["name"] for p in r.json()]
    assert "P2" in names
    assert "P1" not in names


@pytest.mark.asyncio
async def test_search_projects(auth_client):
    sid = await _status_id(auth_client)
    pid = await _priority_id(auth_client)
    await auth_client.post("/api/projects", json={"name": "Alpha Search", "status_id": sid, "priority_id": pid})
    await auth_client.post("/api/projects", json={"name": "Beta Other", "status_id": sid, "priority_id": pid})
    r = await auth_client.get("/api/projects", params={"search": "Alpha"})
    assert r.status_code == 200
    names = [p["name"] for p in r.json()]
    assert any("Alpha" in n for n in names)


@pytest.mark.asyncio
async def test_get_nonexistent_project(auth_client):
    r = await auth_client.get("/api/projects/99999")
    assert r.status_code == 404
