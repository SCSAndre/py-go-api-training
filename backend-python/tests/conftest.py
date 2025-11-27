"""
Pytest configuration and fixtures for testing.

This file contains shared fixtures that can be used across all tests.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.core.database import Base, get_db
from src.core.auth import get_password_hash, create_access_token
from src.models.user import User, UserRole

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database session override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing with valid password."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",  # Valid password with all requirements
        "role": "user"
    }


@pytest.fixture
def sample_admin_data():
    """Sample admin user data for testing."""
    return {
        "email": "admin@example.com",
        "password": "AdminPassword123!",
        "role": "admin"
    }


@pytest.fixture
def sample_book_data():
    """Sample book data for testing."""
    return {
        "title": "Test Book",
        "author": "Test Author",
        "isbn": "978-0123456789",
        "published_date": "2023-01-15",
        "description": "A test book"
    }


@pytest.fixture
def test_user(db_session):
    """Create a test user in the database."""
    user = User(
        email="testuser@example.com",
        hashed_password=get_password_hash("TestPassword123!"),
        role=UserRole.USER
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session):
    """Create an admin user in the database."""
    user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("AdminPassword123!"),
        role=UserRole.ADMIN
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def user_token(test_user):
    """Create a valid JWT token for the test user."""
    token = create_access_token(data={"sub": test_user.email, "user_id": test_user.id})
    return token


@pytest.fixture
def admin_token(admin_user):
    """Create a valid JWT token for the admin user."""
    token = create_access_token(data={"sub": admin_user.email, "user_id": admin_user.id})
    return token


@pytest.fixture
def auth_headers(user_token):
    """Create authentication headers for the test user."""
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def admin_auth_headers(admin_token):
    """Create authentication headers for the admin user."""
    return {"Authorization": f"Bearer {admin_token}"}
