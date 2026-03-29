import pytest


@pytest.mark.asyncio
async def test_list_employees_empty(auth_client):
    r = await auth_client.get("/api/employees")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_create_employee(auth_client):
    r = await auth_client.post("/api/employees", json={
        "full_name": "Ivan Petrov",
        "role": "Developer",
        "email": "ivan@example.com",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["full_name"] == "Ivan Petrov"
    assert data["is_active"] is True
    return data["id"]


@pytest.mark.asyncio
async def test_create_employee_missing_fields(auth_client):
    r = await auth_client.post("/api/employees", json={"full_name": "No Role"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_get_employee(auth_client):
    r = await auth_client.post("/api/employees", json={"full_name": "Anna K", "role": "QA"})
    emp_id = r.json()["id"]
    r2 = await auth_client.get(f"/api/employees/{emp_id}")
    assert r2.status_code == 200
    assert r2.json()["full_name"] == "Anna K"


@pytest.mark.asyncio
async def test_update_employee(auth_client):
    r = await auth_client.post("/api/employees", json={"full_name": "Old Name", "role": "Dev"})
    emp_id = r.json()["id"]
    r2 = await auth_client.patch(f"/api/employees/{emp_id}", json={"full_name": "New Name"})
    assert r2.status_code == 200
    assert r2.json()["full_name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_employee_soft(auth_client):
    r = await auth_client.post("/api/employees", json={"full_name": "Temp User", "role": "Intern"})
    emp_id = r.json()["id"]
    r2 = await auth_client.delete(f"/api/employees/{emp_id}")
    assert r2.status_code == 204
    # Should not appear in active list
    r3 = await auth_client.get("/api/employees")
    ids = [e["id"] for e in r3.json()]
    assert emp_id not in ids


@pytest.mark.asyncio
async def test_get_nonexistent_employee(auth_client):
    r = await auth_client.get("/api/employees/99999")
    assert r.status_code == 404
