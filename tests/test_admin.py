from uuid import uuid4


def _register_user(client):
    """Register a fresh regular-role user and return their id."""
    uid = uuid4().hex[:8]
    payload = {"email": f"target_{uid}@example.com", "username": f"target_{uid}", "password": "testpass123"}
    client.post("/auth/register", json=payload)
    token = client.post("/auth/login", json={"email": payload["email"], "password": payload["password"]}).json()["access_token"]
    return client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).json()["id"]


# ── Access control: unauthenticated → 401 ────────────────────────────────────
# Auth guard fires before route logic; user_id=1 in the path is never reached.

def test_unauthenticated_list_users_returns_401(client):
    response = client.get("/admin/users")

    assert response.status_code == 401


def test_unauthenticated_get_user_returns_401(client):
    response = client.get("/admin/users/1")

    assert response.status_code == 401


def test_unauthenticated_patch_role_returns_401(client):
    response = client.patch("/admin/users/1/role", json={"new_role": "admin"})

    assert response.status_code == 401


def test_unauthenticated_patch_status_returns_401(client):
    response = client.patch("/admin/users/1/status")

    assert response.status_code == 401


def test_unauthenticated_delete_user_returns_401(client):
    response = client.delete("/admin/users/1")

    assert response.status_code == 401


def test_unauthenticated_stats_returns_401(client):
    response = client.get("/admin/stats/overview")

    assert response.status_code == 401


def test_unauthenticated_audit_log_returns_401(client):
    response = client.get("/admin/audit-log")

    assert response.status_code == 401


# ── Access control: regular user (role="user") → 403 ────────────────────────

def test_regular_user_list_users_returns_403(client, auth_headers):
    response = client.get("/admin/users", headers=auth_headers)

    assert response.status_code == 403


def test_regular_user_get_user_returns_403(client, auth_headers):
    response = client.get("/admin/users/99999", headers=auth_headers)

    assert response.status_code == 403


def test_regular_user_patch_role_returns_403(client, auth_headers):
    response = client.patch("/admin/users/99999/role", json={"new_role": "admin"}, headers=auth_headers)

    assert response.status_code == 403


def test_regular_user_patch_status_returns_403(client, auth_headers):
    response = client.patch("/admin/users/99999/status", headers=auth_headers)

    assert response.status_code == 403


def test_regular_user_delete_returns_403(client, auth_headers):
    response = client.delete("/admin/users/99999", headers=auth_headers)

    assert response.status_code == 403


def test_regular_user_stats_returns_403(client, auth_headers):
    response = client.get("/admin/stats/overview", headers=auth_headers)

    assert response.status_code == 403


def test_regular_user_audit_log_returns_403(client, auth_headers):
    response = client.get("/admin/audit-log", headers=auth_headers)

    assert response.status_code == 403


# ── Access control: admin blocked from superadmin-only endpoints → 403 ───────

def test_admin_cannot_change_role(client, admin_user):
    # PATCH /role requires superadmin; admin role is insufficient
    response = client.patch("/admin/users/99999/role", json={"new_role": "user"}, headers=admin_user)

    assert response.status_code == 403


def test_admin_cannot_delete_user(client, admin_user):
    # DELETE requires superadmin; admin role is insufficient
    response = client.delete("/admin/users/99999", headers=admin_user)

    assert response.status_code == 403


# ── Access control: admin can reach read and status endpoints ─────────────────

def test_admin_can_list_users(client, admin_user):
    response = client.get("/admin/users", headers=admin_user)

    assert response.status_code == 200


def test_admin_can_get_stats(client, admin_user):
    response = client.get("/admin/stats/overview", headers=admin_user)

    assert response.status_code == 200


def test_admin_can_get_audit_log(client, admin_user):
    response = client.get("/admin/audit-log", headers=admin_user)

    assert response.status_code == 200


def test_admin_can_get_user_by_id(client, admin_user):
    # Fetching any existing user is allowed for admin
    target_id = _register_user(client)

    response = client.get(f"/admin/users/{target_id}", headers=admin_user)

    assert response.status_code == 200


def test_admin_can_toggle_user_status(client, admin_user):
    # Status toggle is allowed for admin
    target_id = _register_user(client)

    response = client.patch(f"/admin/users/{target_id}/status", headers=admin_user)

    assert response.status_code == 200


# ── GET /admin/users ──────────────────────────────────────────────────────────

def test_list_users_pagination_shape(client, admin_user):
    # Response envelope matches PaginatedUsersResponse
    response = client.get("/admin/users", headers=admin_user)

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_pages" in data
    assert isinstance(data["items"], list)


def test_list_users_items_include_job_count(client, admin_user):
    # Every user object in the list exposes a job_count field
    response = client.get("/admin/users", headers=admin_user)

    items = response.json()["items"]
    assert len(items) >= 1
    assert all("job_count" in u for u in items)


def test_list_users_role_filter(client, admin_user):
    # ?role=admin returns only users whose role is "admin"
    _register_user(client)  # adds a plain "user"-role account

    response = client.get("/admin/users?role=admin", headers=admin_user)

    data = response.json()
    assert data["total"] >= 1
    assert all(u["role"] == "admin" for u in data["items"])


def test_list_users_is_active_filter(client, admin_user):
    # ?is_active=false returns only deactivated users
    target_id = _register_user(client)
    client.patch(f"/admin/users/{target_id}/status", headers=admin_user)  # deactivate

    response = client.get("/admin/users?is_active=false", headers=admin_user)

    data = response.json()
    assert data["total"] >= 1
    assert all(not u["is_active"] for u in data["items"])


# ── GET /admin/users/{user_id} ────────────────────────────────────────────────

def test_get_user_returns_correct_user(client, admin_user):
    # Response includes the correct id and all UserAdminResponse fields
    target_id = _register_user(client)

    response = client.get(f"/admin/users/{target_id}", headers=admin_user)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == target_id
    assert "email" in data
    assert "username" in data
    assert "role" in data
    assert "is_active" in data
    assert "job_count" in data


def test_get_user_not_found_returns_404(client, admin_user):
    # A user_id that does not exist returns 404
    response = client.get("/admin/users/99999", headers=admin_user)

    assert response.status_code == 404


# ── PATCH /admin/users/{user_id}/role ────────────────────────────────────────

def test_change_role_updates_and_returns_user(client, superadmin_user):
    # New role is persisted and reflected in the response body
    target_id = _register_user(client)

    response = client.patch(
        f"/admin/users/{target_id}/role",
        json={"new_role": "admin"},
        headers=superadmin_user,
    )

    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_change_role_rejects_invalid_value(client, superadmin_user):
    # A role string outside the allowed set returns 422
    target_id = _register_user(client)

    response = client.patch(
        f"/admin/users/{target_id}/role",
        json={"new_role": "owner"},
        headers=superadmin_user,
    )

    assert response.status_code == 422


# ── PATCH /admin/users/{user_id}/status ──────────────────────────────────────

def test_toggle_status_deactivates_active_user(client, admin_user):
    # First toggle on an active (default) user sets is_active to False
    target_id = _register_user(client)

    response = client.patch(f"/admin/users/{target_id}/status", headers=admin_user)

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_toggle_status_reactivates_inactive_user(client, admin_user):
    # Second toggle restores is_active to True
    target_id = _register_user(client)
    client.patch(f"/admin/users/{target_id}/status", headers=admin_user)  # deactivate

    response = client.patch(f"/admin/users/{target_id}/status", headers=admin_user)

    assert response.status_code == 200
    assert response.json()["is_active"] is True


# ── DELETE /admin/users/{user_id} ─────────────────────────────────────────────

def test_delete_user_removes_them(client, superadmin_user):
    # 204 is returned; a subsequent GET for that id returns 404
    target_id = _register_user(client)

    response = client.delete(f"/admin/users/{target_id}", headers=superadmin_user)

    assert response.status_code == 204
    assert client.get(f"/admin/users/{target_id}", headers=superadmin_user).status_code == 404


def test_delete_nonexistent_user_returns_404(client, superadmin_user):
    # Deleting a user_id that was never created returns 404
    response = client.delete("/admin/users/99999", headers=superadmin_user)

    assert response.status_code == 404


# ── GET /admin/stats/overview ─────────────────────────────────────────────────

def test_stats_overview_shape(client, admin_user):
    # All required keys are present and jobs_by_status is a mapping
    response = client.get("/admin/stats/overview", headers=admin_user)

    assert response.status_code == 200
    data = response.json()
    assert "total_users" in data
    assert "active_users" in data
    assert "total_jobs" in data
    assert "jobs_by_status" in data
    assert isinstance(data["jobs_by_status"], dict)


def test_stats_counts_match_db_state(client, admin_user):
    # admin_user fixture seeds exactly one active user; no jobs exist yet
    response = client.get("/admin/stats/overview", headers=admin_user)

    data = response.json()
    assert data["total_users"] == 1
    assert data["active_users"] == 1
    assert data["total_jobs"] == 0


# ── GET /admin/audit-log ──────────────────────────────────────────────────────

def test_audit_log_pagination_shape(client, admin_user):
    # Envelope matches PaginatedAuditLogResponse
    response = client.get("/admin/audit-log", headers=admin_user)

    assert response.status_code == 200
    data = response.json()
    for key in ("items", "total", "page", "page_size", "total_pages"):
        assert key in data
    assert isinstance(data["items"], list)


def test_audit_log_newest_first(client, superadmin_user):
    # Multiple entries are returned with the most recent created_at first
    target_id = _register_user(client)
    client.patch(f"/admin/users/{target_id}/role", json={"new_role": "admin"}, headers=superadmin_user)
    client.patch(f"/admin/users/{target_id}/status", headers=superadmin_user)

    entries = client.get("/admin/audit-log", headers=superadmin_user).json()["items"]

    assert len(entries) >= 2
    assert entries[0]["created_at"] >= entries[1]["created_at"]


# ── Audit log entries created by mutations ────────────────────────────────────

def test_role_change_writes_audit_entry(client, superadmin_user):
    # A user.role_change entry appears in the audit log after a role update
    target_id = _register_user(client)
    client.patch(f"/admin/users/{target_id}/role", json={"new_role": "admin"}, headers=superadmin_user)

    entries = client.get("/admin/audit-log", headers=superadmin_user).json()["items"]

    assert any(
        e["action"] == "user.role_change" and e["target_id"] == target_id
        for e in entries
    )


def test_status_toggle_writes_audit_entry(client, admin_user):
    # A user.deactivate entry appears in the audit log after a status toggle
    target_id = _register_user(client)
    client.patch(f"/admin/users/{target_id}/status", headers=admin_user)

    entries = client.get("/admin/audit-log", headers=admin_user).json()["items"]

    assert any(
        e["action"] == "user.deactivate" and e["target_id"] == target_id
        for e in entries
    )


def test_delete_writes_audit_entry(client, superadmin_user):
    # A user.delete entry appears in the audit log after a deletion
    target_id = _register_user(client)
    client.delete(f"/admin/users/{target_id}", headers=superadmin_user)

    entries = client.get("/admin/audit-log", headers=superadmin_user).json()["items"]

    assert any(
        e["action"] == "user.delete" and e["target_id"] == target_id
        for e in entries
    )
