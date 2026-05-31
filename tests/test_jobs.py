from uuid import uuid4

JOB_PAYLOAD = {
    "company_name": "Acme Corp",
    "job_title": "Software Engineer",
    "applied_date": "2026-01-15",
    "status": "applied",
}


def _make_user(client):
    """Register a fresh user and return their auth headers."""
    uid = uuid4().hex[:8]
    client.post("/auth/register", json={
        "email": f"u_{uid}@test.com",
        "username": f"u_{uid}",
        "password": "testpass123",
    })
    resp = client.post("/auth/login", json={
        "email": f"u_{uid}@test.com",
        "password": "testpass123",
    })
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


# ── GET /jobs ─────────────────────────────────────────────────────────────────

def test_list_jobs_empty_for_new_user(client, auth_headers):
    # A brand-new user has no jobs
    response = client.get("/jobs", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []


def test_list_jobs_returns_created_jobs(client, auth_headers):
    # Jobs created by the user appear in the list
    client.post("/jobs", json=JOB_PAYLOAD, headers=auth_headers)
    client.post("/jobs", json={**JOB_PAYLOAD, "company_name": "Beta Ltd"}, headers=auth_headers)

    response = client.get("/jobs", headers=auth_headers)

    assert response.status_code == 200
    assert len(response.json()) == 2


# ── POST /jobs ────────────────────────────────────────────────────────────────

def test_create_job_success(client, auth_headers):
    # Valid payload returns 201 with all fields populated
    response = client.post("/jobs", json=JOB_PAYLOAD, headers=auth_headers)

    assert response.status_code == 201
    data = response.json()
    assert data["company_name"] == JOB_PAYLOAD["company_name"]
    assert data["job_title"] == JOB_PAYLOAD["job_title"]
    assert data["status"] == "applied"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_job_missing_required_field(client, auth_headers):
    # Omitting company_name returns 422
    payload = {k: v for k, v in JOB_PAYLOAD.items() if k != "company_name"}

    response = client.post("/jobs", json=payload, headers=auth_headers)

    assert response.status_code == 422


# ── GET /jobs/{id} ────────────────────────────────────────────────────────────

def test_get_job_success(client, auth_headers, sample_job):
    # Owner can retrieve their job by ID
    response = client.get(f"/jobs/{sample_job['id']}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["id"] == sample_job["id"]


def test_get_job_not_found(client, auth_headers):
    # Non-existent ID returns 404
    response = client.get("/jobs/99999", headers=auth_headers)

    assert response.status_code == 404


def test_get_job_forbidden_other_users_job(client):
    # A user cannot read a job that belongs to someone else
    headers_a = _make_user(client)
    headers_b = _make_user(client)
    job = client.post("/jobs", json=JOB_PAYLOAD, headers=headers_a).json()

    response = client.get(f"/jobs/{job['id']}", headers=headers_b)

    assert response.status_code == 403


# ── PUT /jobs/{id} ────────────────────────────────────────────────────────────

def test_update_job_success(client, auth_headers, sample_job):
    # Partial update returns 200, applies changes, and updated_at is refreshed
    response = client.put(
        f"/jobs/{sample_job['id']}",
        json={"company_name": "New Corp", "status": "offer"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["company_name"] == "New Corp"
    assert data["status"] == "offer"
    assert data["updated_at"] >= sample_job["updated_at"]


def test_update_job_not_found(client, auth_headers):
    # Updating a non-existent job returns 404
    response = client.put(
        "/jobs/99999",
        json={"company_name": "Ghost Corp"},
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_update_job_forbidden_other_users_job(client):
    # A user cannot update a job that belongs to someone else
    headers_a = _make_user(client)
    headers_b = _make_user(client)
    job = client.post("/jobs", json=JOB_PAYLOAD, headers=headers_a).json()

    response = client.put(
        f"/jobs/{job['id']}",
        json={"company_name": "Hijacked"},
        headers=headers_b,
    )

    assert response.status_code == 403


# ── DELETE /jobs/{id} ─────────────────────────────────────────────────────────

def test_delete_job_success(client, auth_headers, sample_job):
    # Owner can delete their job; it is gone on subsequent GET
    response = client.delete(f"/jobs/{sample_job['id']}", headers=auth_headers)

    assert response.status_code == 204
    assert client.get(f"/jobs/{sample_job['id']}", headers=auth_headers).status_code == 404


def test_delete_job_not_found(client, auth_headers):
    # Deleting a non-existent job returns 404
    response = client.delete("/jobs/99999", headers=auth_headers)

    assert response.status_code == 404


def test_delete_job_forbidden_other_users_job(client):
    # A user cannot delete a job that belongs to someone else
    headers_a = _make_user(client)
    headers_b = _make_user(client)
    job = client.post("/jobs", json=JOB_PAYLOAD, headers=headers_a).json()

    response = client.delete(f"/jobs/{job['id']}", headers=headers_b)

    assert response.status_code == 403
