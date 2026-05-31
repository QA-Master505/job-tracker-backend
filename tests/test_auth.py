from uuid import uuid4


def _unique_user():
    uid = uuid4().hex[:8]
    return {
        "email": f"user_{uid}@example.com",
        "username": f"user_{uid}",
        "password": "testpass123",
    }


# ── POST /auth/register ──────────────────────────────────────────────────────

def test_register_success(client):
    # Valid payload returns 201 with user fields; no password in response
    payload = _unique_user()

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["username"] == payload["username"]
    assert "id" in data
    assert "hashed_password" not in data


def test_register_duplicate_email(client):
    # Second registration with the same email returns 409
    payload = _unique_user()
    client.post("/auth/register", json=payload)
    duplicate = {**payload, "username": f"other_{uuid4().hex[:8]}"}

    response = client.post("/auth/register", json=duplicate)

    assert response.status_code == 409


def test_register_duplicate_username(client):
    # Second registration with the same username returns 409
    payload = _unique_user()
    client.post("/auth/register", json=payload)
    duplicate = {**payload, "email": f"other_{uuid4().hex[:8]}@example.com"}

    response = client.post("/auth/register", json=duplicate)

    assert response.status_code == 409


def test_register_short_password(client):
    # Password under 8 characters is rejected with 422
    payload = {**_unique_user(), "password": "short"}

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 422


def test_register_short_username(client):
    # Username under 3 characters is rejected with 422
    payload = {**_unique_user(), "username": "ab"}

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 422


# ── POST /auth/login ─────────────────────────────────────────────────────────

def test_login_success(client, registered_user):
    # Valid credentials return 200 with a bearer access_token
    response = client.post("/auth/login", json={
        "email": registered_user["email"],
        "password": registered_user["password"],
    })

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, registered_user):
    # Correct email but wrong password returns 401
    response = client.post("/auth/login", json={
        "email": registered_user["email"],
        "password": "wrongpassword",
    })

    assert response.status_code == 401


def test_login_unknown_email(client):
    # Email that was never registered returns 401
    response = client.post("/auth/login", json={
        "email": "nobody@example.com",
        "password": "testpass123",
    })

    assert response.status_code == 401


# ── GET /auth/me ─────────────────────────────────────────────────────────────

def test_get_me_authenticated(client, auth_headers, registered_user):
    # Valid token returns 200 with the authenticated user's profile
    response = client.get("/auth/me", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == registered_user["email"]
    assert data["username"] == registered_user["username"]


def test_get_me_unauthenticated(client):
    # Missing Authorization header returns 401
    response = client.get("/auth/me")

    assert response.status_code == 401


# ── POST /auth/logout ─────────────────────────────────────────────────────────

def test_logout_success(client, auth_headers):
    # Valid token returns 200 with a success message
    response = client.post("/auth/logout", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["message"] == "Successfully logged out"


# ── DELETE /users/me ──────────────────────────────────────────────────────────

def test_delete_account_returns_204(client, auth_headers):
    # DELETE /users/me returns 204 No Content
    response = client.delete("/users/me", headers=auth_headers)

    assert response.status_code == 204


def test_delete_account_invalidates_access(client, auth_headers):
    # After deletion, the same token no longer resolves a user — GET /auth/me returns 401
    client.delete("/users/me", headers=auth_headers)

    response = client.get("/auth/me", headers=auth_headers)

    assert response.status_code == 401
