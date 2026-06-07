import pytest
from sqlalchemy.orm import Session
from app.database import engine
from app.models.user import User
from app.models.job_application import JobApplication
from app.models.interview_round import InterviewRound
from app.models.audit_log import AuditLog


@pytest.fixture(scope="function")
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()

    

