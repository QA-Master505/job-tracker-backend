import pytest
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from sqlalchemy import text



def test_unique_email(db_session):
    user1 = User(email='test@example.com', username='testuser1', hashed_password='$2b$12$fakehashedvalue')
    db_session.add(user1)
    db_session.flush()

    user2 = User(email='test@example.com', username='testuser2', hashed_password='$2b$12$fakehashedvalue')
    db_session.add(user2)

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_unique_username(db_session):
    user1 = User(email='test1@example.com', username='testuser1', hashed_password='$2b$12$fakehashedvalue')
    db_session.add(user1)
    db_session.flush()

    user2 = User(email='test2@example.com', username='testuser1', hashed_password='$2b$12$fakehashedvalue')
    db_session.add(user2)

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_is_active_not_null(db_session):
    with pytest.raises(IntegrityError):
        db_session.execute(
            text("INSERT INTO users (email, username, hashed_password, is_active) VALUES ('test@example.com', 'testuser', '$2b$12$fakehashedvalue', NULL)")
        )
    

def test_hashed_password_starts_with_bcrypt(db_session):
    user = User(email='test@example.com', username='testuser', hashed_password='$2b$12$fakehashedvalue')
    db_session.add(user)
    db_session.flush()

    assert user.hashed_password.startswith('$2b$')


def test_default_role_is_user(db_session):
    user = User(email='test@example.com', username='testuser', hashed_password='$2b$12$fakehashedvalue')
    db_session.add(user)
    db_session.flush()

    assert user.role == 'user'