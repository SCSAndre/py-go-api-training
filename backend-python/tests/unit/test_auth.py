"""
Unit tests for authentication and security features.

Tests cover:
- Token validation (missing user_id)
- Email change with password verification
- Email normalization
- Password validation
"""
import pytest
from jose import jwt

from src.core.auth import create_access_token, get_current_user
from src.core.config import settings
from src.models.user import User, UserRole
from src.schemas.user import UserCreate, UserLogin, UserUpdate


class TestTokenValidation:
    """Tests for JWT token validation."""

    def test_token_without_user_id_returns_401(self, client):
        """Token without user_id should return 401 Unauthorized."""
        # Create a token without user_id
        token = jwt.encode(
            {"sub": "test@example.com"},  # Missing user_id
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )

        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 401
        assert response.json()["detail"] == "Could not validate credentials"

    def test_token_without_email_returns_401(self, client, test_user):
        """Token without email (sub) should return 401 Unauthorized."""
        # Create a token without email
        token = jwt.encode(
            {"user_id": test_user.id},  # Missing sub (email)
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )

        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 401
        assert response.json()["detail"] == "Could not validate credentials"

    def test_valid_token_returns_user(self, client, test_user, auth_headers):
        """Valid token with both email and user_id should return user."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["email"] == test_user.email


class TestEmailChangeWithPassword:
    """Tests for email change requiring password verification."""

    def test_email_change_without_password_returns_400(self, client, test_user, auth_headers):
        """Changing email without current password should return 400."""
        response = client.put(
            "/api/v1/auth/me",
            json={"email": "newemail@example.com"},
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Current password required to change email"

    def test_email_change_with_wrong_password_returns_400(self, client, test_user, auth_headers):
        """Changing email with wrong password should return 400."""
        response = client.put(
            "/api/v1/auth/me",
            json={"email": "newemail@example.com", "current_password": "WrongPassword123!"},
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Current password is incorrect"

    def test_email_change_with_correct_password_succeeds(self, client, test_user, auth_headers):
        """Changing email with correct password should succeed."""
        response = client.put(
            "/api/v1/auth/me",
            json={"email": "newemail@example.com", "current_password": "TestPassword123!"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["email"] == "newemail@example.com"

    def test_same_email_without_password_succeeds(self, client, test_user, auth_headers):
        """Setting same email should not require password."""
        response = client.put(
            "/api/v1/auth/me",
            json={"email": test_user.email},
            headers=auth_headers,
        )

        assert response.status_code == 200


class TestEmailNormalization:
    """Tests for email normalization to lowercase."""

    def test_registration_normalizes_email(self, client):
        """Registration should normalize email to lowercase."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "TEST@Example.COM",
                "password": "TestPassword123!",
                "role": "user",
            },
        )

        assert response.status_code == 201
        assert response.json()["email"] == "test@example.com"

    def test_login_normalizes_email(self, client, test_user):
        """Login should work with different email case."""
        # Login with different case
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "TESTUSER@EXAMPLE.COM", "password": "TestPassword123!"},
        )

        assert response.status_code == 200
        assert "access_token" in response.json()


class TestPasswordValidation:
    """Tests for password strength validation."""

    def test_password_too_short_rejected(self, client):
        """Password less than 8 characters should be rejected."""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "Short1!", "role": "user"},
        )

        assert response.status_code == 422
        assert "8 characters" in str(response.json())

    def test_password_without_lowercase_rejected(self, client):
        """Password without lowercase letter should be rejected."""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "PASSWORD123!", "role": "user"},
        )

        assert response.status_code == 422
        assert "lowercase" in str(response.json())

    def test_password_without_uppercase_rejected(self, client):
        """Password without uppercase letter should be rejected."""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "password123!", "role": "user"},
        )

        assert response.status_code == 422
        assert "uppercase" in str(response.json())

    def test_password_without_digit_rejected(self, client):
        """Password without digit should be rejected."""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "Password!!!", "role": "user"},
        )

        assert response.status_code == 422
        assert "digit" in str(response.json())

    def test_password_without_special_char_rejected(self, client):
        """Password without special character should be rejected."""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "Password123", "role": "user"},
        )

        assert response.status_code == 422
        assert "special character" in str(response.json())

    def test_valid_password_accepted(self, client):
        """Valid password should be accepted."""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "ValidPassword123!", "role": "user"},
        )

        assert response.status_code == 201
