"""
Authentication endpoints.

This module handles user registration, login, and profile management.
"""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from src.core.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password,
)
from src.core.config import settings
from src.core.database import get_db
from src.models.user import User
from src.schemas.user import (
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)

router = APIRouter()

# Create a limiter instance for this router
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)) -> User:
    """
    Register a new user.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        The created user

    Raises:
        HTTPException: If email already exists
    """
    # Check if user with this email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    # Create new user with hashed password
    db_user = User(email=user_data.email, hashed_password=get_password_hash(user_data.password), role=user_data.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, user_data: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    """
    Authenticate user and return JWT token.

    Rate limited to 5 requests per minute.

    Args:
        request: FastAPI request object (required for rate limiting)
        user_data: User login credentials
        db: Database session

    Returns:
        JWT access token

    Raises:
        HTTPException: If credentials are invalid
    """
    user = authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id}, expires_delta=access_token_expires)

    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current user's profile.

    Args:
        current_user: The authenticated user

    Returns:
        Current user's profile
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> User:
    """
    Update current user's profile.

    Requires current password to change email for security.

    Args:
        user_update: User update data
        current_user: The authenticated user
        db: Database session

    Returns:
        Updated user profile

    Raises:
        HTTPException: If email change attempted without password or email already taken
    """
    # Check if user is trying to change their email
    if user_update.email and user_update.email != current_user.email:
        # Require current password for email changes
        if not user_update.current_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Current password required to change email"
            )

        # Verify the current password is correct
        if not verify_password(user_update.current_password, current_user.hashed_password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

        # Check if new email is already taken
        existing_user = db.query(User).filter(User.email == user_update.email).first()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        current_user.email = user_update.email

    db.commit()
    db.refresh(current_user)

    return current_user
