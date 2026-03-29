import pytest

from app.models.user import User
from app.services.auth import hash_password


async def _make_employee(client, name="Test Emp"):
    r = await client.post("/api/employees", json={"full_name": name, "role": "Dev"})
    assert r.status_code == 201
    return r.json()["id"]


async def _make_user(db, email="target@test.com", role="member"):
    user = User(email=email, password_hash=hash_password("secret"), role=role)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.mark.asyncio
async def test_link_user_to_employee(auth_client, db):
    emp_id = await _make_employee(auth_client)
    user = await _make_user(db)

    r = await auth_client.post(f"/api/employees/{emp_id}/link", json={"user_id": user.id})
    assert r.status_code == 200
    assert r.json()["user_id"] == user.id


@pytest.mark.asyncio
async def test_link_shows_in_list(auth_client, db):
    emp_id = await _make_employee(auth_client)
    user = await _make_user(db)
    await auth_client.post(f"/api/employees/{emp_id}/link", json={"user_id": user.id})

    r = await auth_client.get("/api/employees")
    emp = next(e for e in r.json() if e["id"] == emp_id)
    assert emp["user_id"] == user.id


@pytest.mark.asyncio
async def test_unlink_user(auth_client, db):
    emp_id = await _make_employee(auth_client)
    user = await _make_user(db)
    await auth_client.post(f"/api/employees/{emp_id}/link", json={"user_id": user.id})

    r = await auth_client.delete(f"/api/employees/{emp_id}/link")
    assert r.status_code == 200
    assert r.json()["user_id"] is None


@pytest.mark.asyncio
async def test_unlink_not_linked(auth_client):
    emp_id = await _make_employee(auth_client)
    r = await auth_client.delete(f"/api/employees/{emp_id}/link")
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_link_nonexistent_employee(auth_client, db):
    user = await _make_user(db)
    r = await auth_client.post("/api/employees/99999/link", json={"user_id": user.id})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_link_nonexistent_user(auth_client):
    emp_id = await _make_employee(auth_client)
    r = await auth_client.post(f"/api/employees/{emp_id}/link", json={"user_id": 99999})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_link_user_already_linked_to_another(auth_client, db):
    emp1_id = await _make_employee(auth_client, "Emp One")
    emp2_id = await _make_employee(auth_client, "Emp Two")
    user = await _make_user(db)

    await auth_client.post(f"/api/employees/{emp1_id}/link", json={"user_id": user.id})
    r = await auth_client.post(f"/api/employees/{emp2_id}/link", json={"user_id": user.id})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_link_requires_admin(member_client, db):
    emp_id = await _make_employee(member_client, "Emp Member")
    user = await _make_user(db, email="other@test.com")
    r = await member_client.post(f"/api/employees/{emp_id}/link", json={"user_id": user.id})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_unlink_requires_admin(client, db, admin, member):
    # Admin links
    admin_token = (
        await client.post("/api/auth/login", json={"email": "admin@test.com", "password": "secret"})
    ).json()["access_token"]
    client.headers["Authorization"] = f"Bearer {admin_token}"
    emp_id = await _make_employee(client, "Linkable")
    user = await _make_user(db, email="linked@test.com")
    await client.post(f"/api/employees/{emp_id}/link", json={"user_id": user.id})

    # Member tries to unlink
    member_token = (
        await client.post("/api/auth/login", json={"email": "member@test.com", "password": "secret"})
    ).json()["access_token"]
    client.headers["Authorization"] = f"Bearer {member_token}"
    r = await client.delete(f"/api/employees/{emp_id}/link")
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_link_activity_logged(auth_client, db):
    emp_id = await _make_employee(auth_client)
    user = await _make_user(db)
    await auth_client.post(f"/api/employees/{emp_id}/link", json={"user_id": user.id})

    r = await auth_client.get("/api/activity", params={"entity_type": "employee"})
    logs = r.json()
    assert any(l["action"] == "linked" for l in logs)
