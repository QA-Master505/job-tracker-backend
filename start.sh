#!/bin/sh
set -e

echo "=== Checking database state ==="
python3 - <<'EOF'
from app.database import engine
from sqlalchemy import inspect, text

inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"Tables found: {tables}")

has_version_table = "alembic_version" in tables
has_users_table = "users" in tables

if has_version_table and not has_users_table:
    print("Detected stale alembic_version (version recorded but tables missing). Resetting...")
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE alembic_version"))
        conn.commit()
    print("alembic_version dropped — migrations will run from scratch.")
else:
    print(f"State OK — alembic_version: {has_version_table}, users: {has_users_table}")
EOF

echo "=== Running migrations ==="
alembic upgrade head

echo "=== Verifying tables ==="
python3 - <<'EOF'
from app.database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"Tables in database: {tables}")

required = ["users", "job_applications", "interview_rounds"]
missing = [t for t in required if t not in tables]
if missing:
    print(f"ERROR: missing tables: {missing}")
    raise SystemExit(1)
print("All required tables verified.")
EOF

echo "=== Starting server ==="
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
