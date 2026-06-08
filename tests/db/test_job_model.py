import pytest
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from app.models.interview_round import InterviewRound
from app.models.job_application import JobApplication
from sqlalchemy import text

@pytest.fixture(scope="function")
def sample_user(db_session):
    """Create a sample user for testing"""
    user = User(
        email='test@example.com',
        username='testuser',
        hashed_password='$2b$12$fakehashedvalue'
    )
    db_session.add(user)
    db_session.flush()
    return user


def test_foreign_key_enforcement(db_session):
    """Test that inserting a JobApplication with non-existent user_id fails"""
    invalid_application = JobApplication(
        user_id = 999999,
        company_name = "Google",
        job_title = "Senior Software Engineer",
        applied_date = "2026-01-15"
    )
    db_session.add(invalid_application)

    # Should raise IntegrityError due to foreign key constraint
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_cascade_delete_job_applications(db_session, sample_user):
    """Test that deleting a user cascades to delete their job applications"""
    # Create a job application for the sample user
    application = JobApplication(
        user_id=sample_user.id,
        company_name="Amazon",
        job_title="Senior Software Quality Manager",
        applied_date="2026-06-02"
    )
    db_session.add(application)
    db_session.flush()
    
    # Verify the job application exists
    assert db_session.query(JobApplication).filter_by(id=application.id).first() is not None
    
    # Delete the user
    db_session.delete(sample_user)
    db_session.flush()
    
    # Verify the job application was also deleted (cascade)
    assert db_session.query(JobApplication).filter_by(id=application.id).first() is None


def test_cascade_delete_interview_rounds(db_session, sample_user):
    """Test that deleting a user cascades to delete their job applications and Interview Rounds"""
    # Create a job application for the sample user
    application = JobApplication(
        user_id=sample_user.id,
        company_name="Amazon",
        job_title="Senior Software Quality Manager",
        applied_date="2026-06-01"
    )
    db_session.add(application)
    db_session.flush()

    # Create an interview round for the job application
    interview_round = InterviewRound(
        job_application_id=application.id,
        round_number=1,
        interview_type="virtual",
        interview_date="2026-06-09"
    )
    db_session.add(interview_round)
    db_session.flush()
    
    # Verify the job application and interview round exist
    assert db_session.query(JobApplication).filter_by(id=application.id).first() is not None
    assert db_session.query(InterviewRound).filter_by(id=interview_round.id).first() is not None
    
    # Delete the user
    db_session.delete(sample_user)
    db_session.flush()
    
    # Verify both the job application AND interview round were deleted (cascade)
    assert db_session.query(JobApplication).filter_by(id=application.id).first() is None
    assert db_session.query(InterviewRound).filter_by(id=interview_round.id).first() is None


def test_applied_date_not_null(db_session, sample_user):
    """Test that inserting a JobApplication without applied_date fails"""
    with pytest.raises(IntegrityError):
        db_session.execute(
            text("""
                INSERT INTO job_applications (user_id, company_name, job_title) 
                VALUES (:user_id, :company_name, :job_title)
            """),
            {"user_id": sample_user.id, "company_name": "Amazon", "job_title": "Senior Software Quality Manager"}
        )


def test_enum_gap_confirmation(db_session, sample_user):
    """Test that status accepts invalid values in the database (known schema gap)
    
    The status column is VARCHAR in PostgreSQL, not a native enum.
    Pydantic validates at API layer, but direct DB inserts accept invalid values.
    This test confirms the gap - no exception should be raised.
    """
    # Insert a job application with an invalid status value
    db_session.execute(
        text("""
            INSERT INTO job_applications (user_id, company_name, job_title, status, applied_date) 
            VALUES (:user_id, :company_name, :job_title, :status, :applied_date)
        """),
        {
            "user_id": sample_user.id,
            "company_name": "Amazon",
            "job_title": "QA Manager",
            "status": "800",  
            "applied_date": "2026-06-02"
        }
    )
    db_session.flush()
    
    # No assertion needed - if the insert succeeds (no exception), the test passes
    # This documents that the database accepts invalid status values