import pytest

from app.models.reference import ProjectPriority, ProjectStatus


@pytest.fixture(autouse=True)
async def seed_reference(db):
    db.add(ProjectStatus(name="Active", is_default=True))
    db.add(ProjectPriority(name="High", order=1))
    await db.commit()


async def _create_project(client):
    r_s = await client.get("/api/reference/statuses")
    r_p = await client.get("/api/reference/priorities")
    sid = r_s.json()[0]["id"]
    pid = r_p.json()[0]["id"]
    r = await client.post("/api/projects", json={"name": "Log Test", "status_id": sid, "priority_id": pid})
    assert r.status_code == 201
    return r.json()["id"]


@pytest.mark.asyncio
async def test_activity_logged_on_project_create(auth_client):
    await _create_project(auth_client)
    r = await auth_client.get("/api/activity")
    assert r.status_code == 200
    logs = r.json()
    assert any(l["action"] == "created" and l["entity_type"] == "project" for l in logs)


@pytest.mark.asyncio
async def test_activity_logged_on_employee_create(auth_client):
    await auth_client.post("/api/employees", json={"full_name": "Test Emp", "role": "Dev"})
    r = await auth_client.get("/api/activity")
    logs = r.json()
    assert any(l["action"] == "created" and l["entity_type"] == "employee" for l in logs)


@pytest.mark.asyncio
async def test_activity_logged_on_delete(auth_client):
    proj_id = await _create_project(auth_client)
    await auth_client.delete(f"/api/projects/{proj_id}")
    r = await auth_client.get("/api/activity")
    logs = r.json()
    assert any(l["action"] == "deleted" and l["entity_type"] == "project" for l in logs)


@pytest.mark.asyncio
async def test_activity_filter_by_entity_type(auth_client):
    await _create_project(auth_client)
    await auth_client.post("/api/employees", json={"full_name": "Emp", "role": "Dev"})

    r = await auth_client.get("/api/activity", params={"entity_type": "project"})
    assert r.status_code == 200
    logs = r.json()
    assert all(l["entity_type"] == "project" for l in logs)


@pytest.mark.asyncio
async def test_activity_unauthenticated(client):
    r = await client.get("/api/activity")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_activity_member_sees_only_own(client, admin, member):
    # Admin creates a project
    admin_login = await client.post("/api/auth/login", json={"email": "admin@test.com", "password": "secret"})
    admin_token = admin_login.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {admin_token}"
    sid = (await client.get("/api/reference/statuses")).json()[0]["id"]
    pid = (await client.get("/api/reference/priorities")).json()[0]["id"]
    await client.post("/api/projects", json={"name": "Admin Project", "status_id": sid, "priority_id": pid})

    # Member creates an employee
    member_login = await client.post("/api/auth/login", json={"email": "member@test.com", "password": "secret"})
    member_token = member_login.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {member_token}"
    await client.post("/api/employees", json={"full_name": "Mem Emp", "role": "Dev"})

    r = await client.get("/api/activity")
    assert r.status_code == 200
    logs = r.json()
    # Member should only see their own entries
    assert all(l["user_id"] == member.id for l in logs)


@pytest.mark.asyncio
async def test_activity_admin_sees_all(auth_client, member, client):
    # Member creates something
    member_login = await client.post("/api/auth/login", json={"email": "member@test.com", "password": "secret"})
    member_token = member_login.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {member_token}"
    await client.post("/api/employees", json={"full_name": "Mem Emp", "role": "Dev"})

    # Admin checks activity
    r = await auth_client.get("/api/activity")
    assert r.status_code == 200
    logs = r.json()
    # Should include member's entry
    assert any(l["user_id"] == member.id for l in logs)


@pytest.mark.asyncio
async def test_activity_pagination(auth_client):
    for i in range(5):
        await auth_client.post("/api/employees", json={"full_name": f"Emp {i}", "role": "Dev"})

    r = await auth_client.get("/api/activity", params={"limit": 2, "offset": 0})
    assert r.status_code == 200
    assert len(r.json()) == 2

    r2 = await auth_client.get("/api/activity", params={"limit": 2, "offset": 2})
    assert r2.status_code == 200
    ids_page1 = {l["id"] for l in r.json()}
    ids_page2 = {l["id"] for l in r2.json()}
    assert ids_page1.isdisjoint(ids_page2)
