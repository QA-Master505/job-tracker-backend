import subprocess
from sqlalchemy import inspect
from app.database import engine
from pathlib import Path


def test_no_pending_migrations():
    """Test that there are no pending Alembic migrations"""
    # Get project root
    project_root = Path(__file__).parent.parent.parent

    result = subprocess.run(
        ["alembic", "check"],
        capture_output=True,
        text=True,
        cwd=str(project_root)  # Pin to project root so alembic.ini is found
    )
    
    # Return code 0 means no pending migrations
    # Non-zero means there are pending migrations or an error
    assert result.returncode == 0, (
        f"Alembic check failed with return code {result.returncode}\n"
        f"STDOUT: {result.stdout}\n"
        f"STDERR: {result.stderr}"
    )


def test_expected_tables_exist():
    """Test that all expected tables are present in the database
    Uses SQLAlchemy Inspector to read the live database schema
    and verify that the core application tables have been created
    by Alembic migrations. 
    Note: alembic_version table (Alembic's internal tracking table)
    will also exist but we don't need to assert on it.
    """
    # Create an inspector that can read database metadata
    inspector = inspect(engine)

    # Get all table names from the current database
    # This returns a list of strings like:
    # ['users', 'job_applications', 'interview_rounds', 'audit_logs', 'alembic_version']
    actual_tables = inspector.get_table_names()

    # Define the tables that MUST exist for the application to work
    expected_tables = ["users", "job_applications", "interview_rounds", "audit_logs"]

    # Check each expected table exists
    # Using a loop gives better error messages than a set comparison
    for table in expected_tables:
        assert table in actual_tables, (
            f"Expected table '{table}' not found in database.\n"
            f"Found tables: {actual_tables}"
        )


def test_users_table_has_expected_columns():
    """Test that the users table has all expected columns
    
    This test catches drift between the SQLAlchemy model and the actual
    database schema. For example, if a developer renames 'hashed_password'
    to 'password_hash' in the model but forgets to update the migration,
    this test will fail because the column name in the database won't match.
    
    The inspector reads the live database schema, ensuring our assumptions
    about column names match reality after all migrations have run.
    """
    # Create an inspector that can read database metadata
    inspector = inspect(engine)
    
    # Get all columns from the users table
    # get_columns() returns a list of dicts like:
    # [
    #   {"name": "id", "type": Integer, "nullable": False, ...},
    #   {"name": "email", "type": String, "nullable": False, ...},
    #   ...
    # ]
    columns_metadata = inspector.get_columns("users")
    
    # Extract just the column names into a flat list
    actual_columns = [col["name"] for col in columns_metadata]
    
    # Define the columns that MUST exist for the application to work
    expected_columns = ["id", "email", "username", "hashed_password", "role", "is_active"]
    
    # Check each expected column exists
    # Using a loop gives better error messages than a set comparison
    for column in expected_columns:
        assert column in actual_columns, (
            f"Expected column '{column}' not found in users table.\n"
            f"Found columns: {actual_columns}"
        )