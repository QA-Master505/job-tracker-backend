from app.models.user import User
import pytest
from app.services.job_service import get_jobs_paginated
from datetime import date
from app.models.job_application import JobApplication, ApplicationStatus
from sqlalchemy import func


@pytest.fixture(scope="function")
def sample_user(db_session):
    """Create a sample user for testing"""
    user = User(
        email='test@example.com',
        username='testuser',
        hashed_password='$2b$12$fakehashedvalue',
        is_active=True  # (NOT NULL constraint)
    )
    db_session.add(user)
    db_session.flush()  # Flush sends to DB without committing, so rollback can clean up
    return user




@pytest.fixture(scope="function")
def multiple_jobs(db_session, sample_user):
    """Create 7 job applications for pagination testing"""
    jobs = []
    for i in range(1, 8):
        job = JobApplication(
            user_id=sample_user.id,
            company_name=f"Company {i}",
            job_title=f"Position {i}",
            applied_date=date(2026, 6, i),
            status=ApplicationStatus.applied  # Explicitly set status (though default handles it)
        )
        db_session.add(job)  # Stage the job for insertion into database
        jobs.append(job)     # Store in list so test can assert on total count and individual job properties
    db_session.flush()       # Execute all INSERTs in a single batch
    return jobs              # Return list for use in test assertions (e.g., verifying pagination returns the correct subset)


def test_insert_and_retrieve_user(db_session, sample_user):
    """Test that a user can be inserted and retrieved from the database"""
    # Query the database for the user by email
    retrieved_user = db_session.query(User).filter_by(email='test@example.com').first()
    
    # Assert the result is not None
    assert retrieved_user is not None

    # Assert has unique hashed password
    assert retrieved_user.hashed_password.startswith('$2b$')
    
    # Assert the returned username matches what was inserted
    assert retrieved_user.username == 'testuser'


def test_filter_user_by_field(db_session, sample_user):
    """Test that filtering users by field returns the correct record"""
    # Query by username (positive case)
    retrieved_user = db_session.query(User).filter_by(username='testuser').first()
    
    # Assert the result is not None
    assert retrieved_user is not None
    
    # Assert the returned email matches what was inserted
    assert retrieved_user.email == 'test@example.com'

    # Assert the returned hashedpassword matches what was inserted
    assert retrieved_user.hashed_password == '$2b$12$fakehashedvalue'
    
    # Query for a username that does not exist (negative case)
    not_found_user = db_session.query(User).filter_by(username='nonexistentuser').first()
    
    # Assert the result is None when no match exists
    assert not_found_user is None


def test_deleted_user_is_not_retrievable(db_session, sample_user):
    """Test that a deleted user cannot be retrieved from the database"""
    # Step 1: Save the user ID
    user_id = sample_user.id
    
    # Step 2: Delete the user and flush
    db_session.delete(sample_user)
    db_session.flush()
    
    # Step 3: Query by user_id and assert the result is None
    deleted_user = db_session.query(User).filter_by(id=user_id).first()
    assert deleted_user is None


def test_pagination_offset_limit(db_session, sample_user, multiple_jobs):
    """Test that get_jobs_paginated returns correct paginated results"""
    # Call get_jobs_paginated with page=1 and page_size=6
    page2_result = get_jobs_paginated(db_session, sample_user.id, page=2, page_size=6)
    
    # Assertions based on 7 total jobs, page_size=6, page=2
    assert page2_result['total'] == 7           # Total jobs in database
    assert page2_result['total_pages'] == 2     # 7/6 = 1.2 → rounded up to 2 pages
    assert len(page2_result['items']) == 1      # Page 2 should have 2 items (jobs 7)
    assert page2_result['page'] == 2            # Current page number
    assert page2_result['page_size'] == 6       # Items per page requested
    
    # Verify correct items are on page 2 (jobs 3 and 4)
    assert page2_result['items'][0].company_name == "Company 1"


def test_job_count_aggregation(db_session, sample_user, multiple_jobs):
    """Test that job count aggregation returns the correct number of jobs for a user"""
    # Query the count of jobs filtered by sample_user.id
    count = db_session.query(func.count(JobApplication.id)).filter(
        JobApplication.user_id == sample_user.id
    ).scalar() # returns the single value directly
    
     # Assert the count equals 7 (number of jobs created by multiple_jobs fixture)
    assert count == 7


def test_filter_jobs_by_user_id(db_session, sample_user, multiple_jobs):
    """Test that filtering jobs by user_id only returns that user's jobs"""
    
    # Create a second user
    second_user = User(
        email='second@example.com',
        username='seconduser',
        hashed_password='$2b$12$anotherfakehash',
        is_active=True
    )
    db_session.add(second_user)
    db_session.flush()
    
    # Create 2 jobs for the second user
    for i in range(1, 3):
        job = JobApplication(
            user_id=second_user.id,
            company_name=f"Company {i}",
            job_title=f"Position {i}",
            applied_date=date(2026, 6, i),
            status=ApplicationStatus.applied  # Explicitly set status (though default handles it)
        )
        db_session.add(job)
    db_session.flush()
    
    # Query jobs filtered by sample_user.id
    sample_user_jobs = db_session.query(JobApplication).filter(
        JobApplication.user_id == sample_user.id
    ).all()
    
    # Assert all returned jobs belong to sample_user
    assert all(job.user_id == sample_user.id for job in sample_user_jobs)
    assert len(sample_user_jobs) == 7


    # Query jobs filtered by second_user.id
    second_user_jobs = db_session.query(JobApplication).filter(
        JobApplication.user_id == second_user.id
    ).all()
    # Assert all returned jobs belong to second_user
    assert all(job.user_id == second_user.id for job in second_user_jobs)
    assert len(second_user_jobs) == 2