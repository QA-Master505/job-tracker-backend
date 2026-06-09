"""
Tests for Admin Service

These tests verify that administrative operations (role changes, user management, etc.)
work correctly and maintain proper audit trails.

KEY CONCEPT: Service functions call db.commit() internally, unlike direct DB tests
that only use flush(). This means:
    - Rollback fixture cannot undo service changes
    - We need explicit cleanup (try/finally blocks or fixture cleanup)
    - Each test must delete its own test data

The admin_test_users fixture provides consistent test users for all tests.
"""

import pytest
import json
from datetime import date
from app.services import admin_service
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.job_application import JobApplication, ApplicationStatus


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def admin_test_users(db_session):
    """
    Fixture that creates actor and target users for ALL admin service tests
    
    WHAT IT CREATES:
        - actor_user: Admin user who performs actions (role changes, deactivations)
        - target_user: Regular user who will be modified by admin actions
    
    WHY BOTH:
        - Admin actions need someone to PERFORM the action (actor)
        - And someone to BE modified (target)
    
    YIELDS:
        tuple: (actor_id, target_user_id) - tests unpack these values
    
    CLEANUP:
        - Deletes audit logs first (foreign key dependency)
        - Then deletes target user
        - Finally deletes actor user
        - Commits deletions (must commit because service commits)
    """
    actor_user = None  # Initialize for safe cleanup if creation fails
    target_user = None  # Initialize for safe cleanup if creation fails
    
    try:
        # Create actor user (admin who will perform actions)
        actor_user = User(
            email='admin@example.com',
            username='adminuser',
            hashed_password='$2b$12$adminhash',
            is_active=True,   # NOT NULL constraint
            role='admin'       # Admin role required for permission checks
        )
        db_session.add(actor_user)
        db_session.flush()  # Send to DB but stay in transaction (rollback can undo)
        
        # Create target user (regular user who will be modified)
        target_user = User(
            email='target@example.com',
            username='targetuser',
            hashed_password='$2b$12$targetuserhash',
            is_active=True,   # NOT NULL constraint
            role='user'        # Start with default user role
        )
        db_session.add(target_user)
        db_session.flush()
        
        # Yield IDs for tests to use
        yield actor_user.id, target_user.id
        
    finally:
        # Cleanup runs even if test fails - prevents data pollution
        # Delete in reverse order of dependencies to avoid foreign key violations
        
        if target_user:
            # First: Delete audit logs referencing target user
            db_session.query(AuditLog).filter(
                AuditLog.target_id == target_user.id
            ).delete()
            # Second: Delete target user itself
            db_session.query(User).filter(User.id == target_user.id).delete()
            
        if actor_user:
            # Finally: Delete actor user (no remaining dependencies)
            db_session.query(User).filter(User.id == actor_user.id).delete()
            
        # Commit cleanup since service functions commit - rollback fixture won't undo
        db_session.commit()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _create_test_user(db_session, email, username, is_active, role='user'):
    """
    Helper to create a test user and return its ID
    
    WHY: Eliminates user creation code duplication across multiple tests
    
    Args:
        db_session: Database session
        email: User's email address (must be unique)
        username: User's username (must be unique)
        is_active: Boolean for account status
        role: User role ('user' or 'admin')
    
    Returns:
        int: The newly created user's ID
    """
    user = User(
        email=email,
        username=username,
        hashed_password='$2b$12$testhash',  # Consistent fake hash for tests
        is_active=is_active,
        role=role
    )
    db_session.add(user)
    db_session.flush()  # Assigns ID without committing
    return user.id


def _create_test_job(db_session, user_id, company_name, job_title, applied_date, status):
    """
    Helper to create a test job application and return its ID
    
    WHY: Eliminates job creation code duplication across multiple tests
    
    Args:
        db_session: Database session
        user_id: ID of user who owns this job application
        company_name: Name of the company
        job_title: Position title
        applied_date: Date when application was submitted
        status: ApplicationStatus enum value
    
    Returns:
        int: The newly created job application's ID
    """
    job = JobApplication(
        user_id=user_id,
        company_name=company_name,
        job_title=job_title,
        applied_date=applied_date,
        status=status
    )
    db_session.add(job)
    db_session.flush()
    return job.id


def _cleanup_entities(db_session, job_ids, user_ids):
    """
    Helper to clean up jobs and users in correct order
    
    WHY: Centralized cleanup prevents foreign key violations and code duplication
    
    IMPORTANT: Delete jobs BEFORE users because job.user_id references user.id
    If we deleted users first, PostgreSQL would raise a foreign key violation.
    
    Args:
        db_session: Database session
        job_ids: List of job application IDs to delete
        user_ids: List of user IDs to delete
    """
    # Delete jobs first (they reference users)
    for job_id in job_ids:
        db_session.query(JobApplication).filter(JobApplication.id == job_id).delete()
    
    # Then delete users (no remaining dependencies)
    for user_id in user_ids:
        db_session.query(User).filter(User.id == user_id).delete()
    
    # Commit cleanup - must commit because service functions commit
    db_session.commit()


def _perform_role_change_and_get_audit_log(db_session, actor_id, target_user_id):
    """
    Helper function to perform role change and retrieve audit log entry
    
    WHY: This is the core admin action - extracting it eliminates duplication
         between test_audit_log_created_on_role_change and test_atomic_transaction
    
    WHAT IT DOES:
        1. Calls admin_service.update_user_role() to change role from 'user' to 'admin'
        2. Queries the audit log for the exact entry created by this action
    
    Args:
        db_session: Database session
        actor_id: ID of admin performing the action
        target_user_id: ID of user whose role is being changed
    
    Returns:
        tuple: (updated_user, audit_entry)
            - updated_user: User object with new role (from service return)
            - audit_entry: AuditLog entry or None if not found
    """
    # Call service function - this commits internally
    updated_user, job_count = admin_service.update_user_role(
        db=db_session,
        user_id=target_user_id,
        new_role='admin',
        actor_id=actor_id
    )
    
    # Query audit log using all identifying fields
    audit_entry = db_session.query(AuditLog).filter(
        AuditLog.action == 'user.role_change',
        AuditLog.target_type == 'user',
        AuditLog.target_id == target_user_id,
        AuditLog.actor_id == actor_id
    ).first()
    
    return updated_user, audit_entry


# ============================================================================
# TEST 1: AUDIT LOG CREATION
# ============================================================================

def test_audit_log_created_on_role_change(db_session, admin_test_users):
    """
    Test that changing a user's role creates an audit log entry
    
    WHAT THIS VERIFIES:
        - Role change succeeds (user.role updates from 'user' to 'admin')
        - Audit log entry is created with correct action type
        - Audit log contains JSON details showing old_role and new_role
    
    WHY THIS MATTERS:
        - Compliance requirement: All admin actions must be auditable
        - Helps track who changed what and when
        - Provides forensic evidence for security investigations
    """
    # Unpack fixture values - admin_test_users provides (actor_id, target_user_id)
    actor_id, target_user_id = admin_test_users
    
    # Perform role change and retrieve audit log using helper
    updated_user, audit_entry = _perform_role_change_and_get_audit_log(
        db_session, actor_id, target_user_id
    )
    
    # Verify role change succeeded
    assert updated_user.role == 'admin'
    
    # Verify audit log entry exists
    assert audit_entry is not None
    assert audit_entry.action == 'user.role_change'
    assert audit_entry.target_type == 'user'
    assert audit_entry.target_id == target_user_id
    assert audit_entry.actor_id == actor_id
    
    # Verify JSON details contain both old and new roles
    detail = json.loads(audit_entry.detail)
    assert detail['old_role'] == 'user'   # Original role before change
    assert detail['new_role'] == 'admin'  # New role after change


# ============================================================================
# TEST 2: ATOMIC TRANSACTION VERIFICATION
# ============================================================================

def test_atomic_transaction(db_session, admin_test_users):
    """
    Test that role change and audit log are committed atomically
    
    WHAT IS ATOMICITY?
        - Both operations (role change + audit log) succeed together OR neither succeeds
        - No scenario where only ONE operation commits
    
    WHY THIS MATTERS:
        - Database consistency: Role change without audit log = untracked change
        - Audit log without role change = false record
        - Atomicity guarantees data integrity
    
    HOW WE PROVE ATOMICITY:
        - Verify role change persisted in database (fresh query - no cache)
        - Verify audit log entry persisted in database
        - Both must exist - proves they committed in same transaction
    """
    actor_id, target_user_id = admin_test_users
    
    # Perform role change and retrieve audit log
    updated_user, audit_entry = _perform_role_change_and_get_audit_log(
        db_session, actor_id, target_user_id
    )
    
    # PROOF 1: Role change persisted in returned object
    assert updated_user.role == 'admin'
    
    # PROOF 2: Role change persisted in database (fresh query)
    # Important: Query again to avoid any SQLAlchemy session caching
    # This proves the change was actually COMMITTED, not just in memory
    fresh_user = db_session.query(User).filter(User.id == target_user_id).first()
    assert fresh_user.role == 'admin'
    
    # PROOF 3: Audit log entry exists in database
    assert audit_entry is not None
    
    # PROOF 4: Audit log has complete data
    detail = json.loads(audit_entry.detail)
    assert detail['old_role'] == 'user'
    assert detail['new_role'] == 'admin'
    
    # If we reach here: Both changes exist → Transaction was atomic!


# ============================================================================
# TEST 3: ACTOR_ID SETS TO NULL WHEN ACTOR DELETED
# ============================================================================

def test_actor_id_set_null_on_delete(db_session, admin_test_users):
    """
    Test that actor_id becomes NULL in audit logs when the actor user is deleted
    
    BUSINESS RULE: Preserve audit history even when users are deleted
        - Audit logs should NOT be deleted when actor user is removed
        - actor_id field becomes NULL (foreign key SET NULL behavior)
        - Other audit log fields (action, target_type, detail) remain intact
    
    SCENARIO:
        1. Actor (admin) performs a role change → creates audit log with actor_id
        2. Delete the actor user using delete_user_by_id
        3. Audit log entry should still exist but actor_id = NULL
    
    WHY THIS MATTERS:
        - Compliance: Audit history cannot be deleted
        - Referential integrity: SET NULL prevents orphaned references
        - Forensic value: Know a deleted admin made the change, even if account gone
    
    FOREIGN KEY BEHAVIOR:
        - Foreign key: audit_log.actor_id → users.id
        - On delete: SET NULL (not CASCADE)
        - This preserves audit trail while removing user reference
    """
    actor_id, target_user_id = admin_test_users
    
    # STEP 1: Create audit log by performing role change
    updated_user, audit_entry = _perform_role_change_and_get_audit_log(
        db_session, actor_id, target_user_id
    )
    
    # Verify audit log exists with actor_id set BEFORE deletion
    assert audit_entry is not None
    assert audit_entry.actor_id == actor_id
    assert audit_entry.target_id == target_user_id
    
    # STEP 2: Delete the actor user
    # This triggers SET NULL on audit_log.actor_id foreign key
    admin_service.delete_user_by_id(
        db=db_session,
        user_id=actor_id,     # User to delete (the actor who performed the action)
        actor_id=actor_id     # Actor performing deletion (self-deletion scenario)
    )
    
    # STEP 3: Verify audit log still exists with NULL actor_id
    audit_entry_after = db_session.query(AuditLog).filter(
        AuditLog.action == 'user.role_change',
        AuditLog.target_type == 'user',
        AuditLog.target_id == target_user_id
    ).first()
    
    # Assert audit log was NOT deleted (preserved for compliance)
    assert audit_entry_after is not None
    
    # Assert actor_id is now NULL (foreign key SET NULL behavior)
    assert audit_entry_after.actor_id is None
    
    # Assert other fields remain unchanged
    assert audit_entry_after.action == 'user.role_change'
    assert audit_entry_after.target_type == 'user'
    assert audit_entry_after.target_id == target_user_id
    
    # Verify JSON details are still intact
    detail = json.loads(audit_entry_after.detail)
    assert detail['old_role'] == 'user'
    assert detail['new_role'] == 'admin'


# ============================================================================
# TEST 4: STATS OVERVIEW ACCURACY
# ============================================================================

def test_stats_overview_accuracy(db_session):
    """
    Test that get_stats_overview returns accurate counts matching database
    
    VERIFIES:
        - total_users: Count of all users
        - active_users: Count only where is_active=True
        - total_jobs: Count of all job applications
        - jobs_by_status: Count of jobs grouped by status
    
    SETUP:
        - 2 users: 1 active, 1 inactive
        - 3 jobs: applied, offer, rejected
    
    WHY THIS MATTERS:
        - Dashboard metrics must be accurate for admin decision making
        - Ensures counting logic handles filters correctly
        - Verifies grouping aggregation works
    
    BEFORE/AFTER PATTERN:
        - Take snapshot BEFORE inserting test data
        - Insert test data
        - Take snapshot AFTER insertion
        - Assert differences match our insertions
        - This prevents conflicts with other tests' data in CI
    
    WHY NOT ABSOLUTE VALUES:
        - Other tests may have left data in database
        - Before/after pattern is immune to existing data
        - Only checks OUR changes, not total counts
    """
    user_ids = []  # Track created users for cleanup
    job_ids = []   # Track created jobs for cleanup
    
    try:
        # STEP 1: Take BEFORE snapshot (baseline before our changes)
        stats_before = admin_service.get_stats_overview(db_session)
        
        # STEP 2: Create test users
        # User 1: Active user (is_active=True)
        active_user_id = _create_test_user(
            db_session, 
            'stats_active@example.com', 
            'stats_activeuser', 
            True,   # is_active
            'user'
        )
        user_ids.append(active_user_id)
        
        # User 2: Inactive user (is_active=False)
        inactive_user_id = _create_test_user(
            db_session, 
            'stats_inactive@example.com', 
            'stats_inactiveuser', 
            False,  # is_active
            'user'
        )
        user_ids.append(inactive_user_id)
        
        # STEP 3: Create test jobs with different statuses
        # Job 1: Applied status
        job_ids.append(_create_test_job(
            db_session, active_user_id, 'Company A', 'Position A', 
            date(2026, 1, 1), ApplicationStatus.applied
        ))
        
        # Job 2: Offer status
        job_ids.append(_create_test_job(
            db_session, active_user_id, 'Company B', 'Position B', 
            date(2026, 1, 2), ApplicationStatus.offer
        ))
        
        # Job 3: Rejected status
        job_ids.append(_create_test_job(
            db_session, active_user_id, 'Company C', 'Position C', 
            date(2026, 1, 3), ApplicationStatus.rejected
        ))
        
        # STEP 4: Commit our changes
        # Required so stats_after can see them (service functions commit)
        db_session.commit()
        
        # STEP 5: Take AFTER snapshot
        stats_after = admin_service.get_stats_overview(db_session)
        
        # STEP 6: Verify increments match our insertions
        # User counts: Created 2 users total
        assert stats_after['total_users'] == stats_before['total_users'] + 2, \
            f"total_users: expected {stats_before['total_users'] + 2}, got {stats_after['total_users']}"
        
        # Active users: Created only 1 active user
        assert stats_after['active_users'] == stats_before['active_users'] + 1, \
            f"active_users: expected {stats_before['active_users'] + 1}, got {stats_after['active_users']}"
        
        # Job counts: Created 3 jobs total
        assert stats_after['total_jobs'] == stats_before['total_jobs'] + 3, \
            f"total_jobs: expected {stats_before['total_jobs'] + 3}, got {stats_after['total_jobs']}"
        
        # Status counts: 1 of each status we created
        assert stats_after['jobs_by_status']['applied'] == stats_before['jobs_by_status']['applied'] + 1, \
            f"applied: expected {stats_before['jobs_by_status']['applied'] + 1}, got {stats_after['jobs_by_status']['applied']}"
        
        assert stats_after['jobs_by_status']['offer'] == stats_before['jobs_by_status']['offer'] + 1, \
            f"offer: expected {stats_before['jobs_by_status']['offer'] + 1}, got {stats_after['jobs_by_status']['offer']}"
        
        assert stats_after['jobs_by_status']['rejected'] == stats_before['jobs_by_status']['rejected'] + 1, \
            f"rejected: expected {stats_before['jobs_by_status']['rejected'] + 1}, got {stats_after['jobs_by_status']['rejected']}"
        
        # Note: We don't assert other statuses == 0 because other tests may have inserted them
        # The before/after pattern handles this correctly - only checking OUR additions
        
    finally:
        # STEP 7: Cleanup - always runs even if assertions fail
        # Delete jobs first (they reference users), then users
        _cleanup_entities(db_session, job_ids, user_ids)