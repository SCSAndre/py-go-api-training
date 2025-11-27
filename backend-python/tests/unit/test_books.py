"""
Unit tests for book authorization.

Tests cover:
- Book creation ownership
- Book update authorization (owner/admin only)
- Book delete authorization (owner/admin only)
"""
import pytest

from src.models.book import Book
from src.core.auth import get_password_hash, create_access_token
from src.models.user import User, UserRole


class TestBookAuthorization:
    """Tests for book authorization (update/delete)."""

    def test_create_book_sets_created_by(self, client, test_user, auth_headers, sample_book_data):
        """Creating a book should set created_by to current user."""
        response = client.post("/api/v1/books/", json=sample_book_data, headers=auth_headers)

        assert response.status_code == 201
        assert response.json()["created_by"] == test_user.id

    def test_non_owner_cannot_update_book(self, client, db_session, test_user, sample_book_data):
        """Non-owner should not be able to update another user's book."""
        # Create another user
        other_user = User(
            email="other@example.com",
            hashed_password=get_password_hash("OtherPassword123!"),
            role=UserRole.USER,
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)

        # Create a book by other_user
        book = Book(
            title=sample_book_data["title"],
            author=sample_book_data["author"],
            isbn=sample_book_data["isbn"],
            created_by=other_user.id,
        )
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        # Try to update with test_user's token
        test_user_token = create_access_token(data={"sub": test_user.email, "user_id": test_user.id})
        response = client.put(
            f"/api/v1/books/{book.id}",
            json={"title": "Updated Title"},
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "You can only update your own books"

    def test_owner_can_update_book(self, client, db_session, test_user, auth_headers, sample_book_data):
        """Owner should be able to update their own book."""
        # Create a book by test_user
        book = Book(
            title=sample_book_data["title"],
            author=sample_book_data["author"],
            isbn=sample_book_data["isbn"],
            created_by=test_user.id,
        )
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        # Update the book
        response = client.put(
            f"/api/v1/books/{book.id}",
            json={"title": "Updated Title"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    def test_admin_can_update_any_book(self, client, db_session, test_user, admin_user, admin_auth_headers, sample_book_data):
        """Admin should be able to update any user's book."""
        # Create a book by test_user
        book = Book(
            title=sample_book_data["title"],
            author=sample_book_data["author"],
            isbn=sample_book_data["isbn"],
            created_by=test_user.id,
        )
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        # Admin updates the book
        response = client.put(
            f"/api/v1/books/{book.id}",
            json={"title": "Admin Updated Title"},
            headers=admin_auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Admin Updated Title"

    def test_non_owner_cannot_delete_book(self, client, db_session, test_user, sample_book_data):
        """Non-owner should not be able to delete another user's book."""
        # Create another user
        other_user = User(
            email="other@example.com",
            hashed_password=get_password_hash("OtherPassword123!"),
            role=UserRole.USER,
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)

        # Create a book by other_user
        book = Book(
            title=sample_book_data["title"],
            author=sample_book_data["author"],
            isbn=sample_book_data["isbn"],
            created_by=other_user.id,
        )
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        # Try to delete with test_user's token
        test_user_token = create_access_token(data={"sub": test_user.email, "user_id": test_user.id})
        response = client.delete(
            f"/api/v1/books/{book.id}",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "You can only delete your own books"

    def test_owner_can_delete_book(self, client, db_session, test_user, auth_headers, sample_book_data):
        """Owner should be able to delete their own book."""
        # Create a book by test_user
        book = Book(
            title=sample_book_data["title"],
            author=sample_book_data["author"],
            isbn=sample_book_data["isbn"],
            created_by=test_user.id,
        )
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        # Delete the book
        response = client.delete(f"/api/v1/books/{book.id}", headers=auth_headers)

        assert response.status_code == 204

    def test_admin_can_delete_any_book(self, client, db_session, test_user, admin_user, admin_auth_headers, sample_book_data):
        """Admin should be able to delete any user's book."""
        # Create a book by test_user
        book = Book(
            title=sample_book_data["title"],
            author=sample_book_data["author"],
            isbn=sample_book_data["isbn"],
            created_by=test_user.id,
        )
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        # Admin deletes the book
        response = client.delete(f"/api/v1/books/{book.id}", headers=admin_auth_headers)

        assert response.status_code == 204

    def test_unauthenticated_cannot_update_book(self, client, db_session, test_user, sample_book_data):
        """Unauthenticated user should not be able to update a book."""
        # Create a book
        book = Book(
            title=sample_book_data["title"],
            author=sample_book_data["author"],
            isbn=sample_book_data["isbn"],
            created_by=test_user.id,
        )
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        # Try to update without authentication
        response = client.put(f"/api/v1/books/{book.id}", json={"title": "Updated Title"})

        assert response.status_code == 401

    def test_unauthenticated_cannot_delete_book(self, client, db_session, test_user, sample_book_data):
        """Unauthenticated user should not be able to delete a book."""
        # Create a book
        book = Book(
            title=sample_book_data["title"],
            author=sample_book_data["author"],
            isbn=sample_book_data["isbn"],
            created_by=test_user.id,
        )
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        # Try to delete without authentication
        response = client.delete(f"/api/v1/books/{book.id}")

        assert response.status_code == 401
