"""
Book schemas for request/response validation.
"""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class BookBase(BaseModel):
    """Base book schema with common fields."""

    title: str
    author: str
    isbn: Optional[str] = None
    published_date: Optional[date] = None
    description: Optional[str] = None


class BookCreate(BookBase):
    """Schema for creating a new book."""

    pass


class BookUpdate(BaseModel):
    """Schema for updating a book."""

    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None
    published_date: Optional[date] = None
    description: Optional[str] = None


class BookResponse(BookBase):
    """Schema for book response."""

    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
