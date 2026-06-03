#!/usr/bin/env python3
"""Seed a superadmin user into the CI database. Safe to run multiple times."""
import os
import sys

import bcrypt
from sqlalchemy import create_engine, text


def _require_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        print(f"ERROR: {name} is not set", file=sys.stderr)
        sys.exit(1)
    return value


database_url = _require_env("DATABASE_URL")
email        = _require_env("CI_SUPERADMIN_EMAIL")
password     = _require_env("CI_SUPERADMIN_PASSWORD")

# SQLAlchemy 2.x requires postgresql:// — Railway (and some CI providers) supply postgres://
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

engine = create_engine(database_url)
with engine.begin() as conn:
    conn.execute(
        text(
            """
            INSERT INTO users (email, username, hashed_password, role, is_active)
            VALUES (:email, :username, :hashed, 'superadmin', true)
            ON CONFLICT (email) DO NOTHING
            """
        ),
        {"email": email, "username": email.split("@")[0], "hashed": hashed},
    )

print(f"Superadmin seeded: {email}")
