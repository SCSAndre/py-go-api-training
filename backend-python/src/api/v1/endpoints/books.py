"""
Book endpoints.

This module handles CRUD operations for books with proper authorization.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.auth import get_current_user
from src.core.database import get_db
from src.models.book import Book
from src.models.user import User, UserRole
from src.schemas.book import BookCreate, BookResponse, BookUpdate

router = APIRouter()


@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    book_data: BookCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Book:
    """
    Create a new book.

    Args:
        book_data: Book creation data
        current_user: The authenticated user
        db: Database session

    Returns:
        The created book
    """
    db_book = Book(
        title=book_data.title,
        author=book_data.author,
        isbn=book_data.isbn,
        published_date=book_data.published_date,
        description=book_data.description,
        created_by=current_user.id,
    )
    db.add(db_book)
    db.commit()
    db.refresh(db_book)

    return db_book


@router.get("/", response_model=List[BookResponse])
async def list_books(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> List[Book]:
    """
    List all books with pagination.

    Args:
        skip: Number of books to skip
        limit: Maximum number of books to return
        db: Database session

    Returns:
        List of books
    """
    books = db.query(Book).offset(skip).limit(limit).all()
    return books


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(book_id: int, db: Session = Depends(get_db)) -> Book:
    """
    Get a specific book by ID.

    Args:
        book_id: The book's ID
        db: Database session

    Returns:
        The requested book

    Raises:
        HTTPException: If book not found
    """
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return db_book


@router.put("/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: int, book_update: BookUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Book:
    """
    Update a book.

    Only the book's creator or an admin can update the book.

    Args:
        book_id: The book's ID
        book_update: Book update data
        current_user: The authenticated user
        db: Database session

    Returns:
        The updated book

    Raises:
        HTTPException: If book not found or user not authorized
    """
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    # Authorization check: only the creator or an admin can update
    if db_book.created_by != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only update your own books")

    # Update fields if provided
    update_data = book_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_book, field, value)

    db.commit()
    db.refresh(db_book)

    return db_book


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    """
    Delete a book.

    Only the book's creator or an admin can delete the book.

    Args:
        book_id: The book's ID
        current_user: The authenticated user
        db: Database session

    Raises:
        HTTPException: If book not found or user not authorized
    """
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    # Authorization check: only the creator or an admin can delete
    if db_book.created_by != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only delete your own books")

    db.delete(db_book)
    db.commit()
