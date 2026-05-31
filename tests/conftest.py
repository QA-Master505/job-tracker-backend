import os

# Must be set before app modules are imported — pydantic-settings reads at module load.
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-tests")

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.main import app
from app.models.base import Base

SQLITE_URL = "sqlite://"


@pytest.fixture(scope="function")
def _test_engine():
    engine = create_engine(
        SQLITE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db(_test_engine):
    session = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(_test_engine):
    factory = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)

    def override_get_db():
        session = factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def registered_user(client):
    uid = uuid4().hex[:8]
    payload = {
        "email": f"user_{uid}@example.com",
        "username": f"user_{uid}",
        "password": "testpass123",
    }
    client.post("/auth/register", json=payload)
    return payload


@pytest.fixture(scope="function")
def auth_headers(client, registered_user):
    resp = client.post("/auth/login", json={
        "email": registered_user["email"],
        "password": registered_user["password"],
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def sample_job(client, auth_headers):
    resp = client.post("/jobs", json={
        "company_name": "Acme Corp",
        "job_title": "Software Engineer",
        "applied_date": "2026-01-15",
        "status": "applied",
    }, headers=auth_headers)
    return resp.json()
