# api/user.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from database.models import User
import crud.user as user_crud
from schemas.user import UserResponse, UserCreate
from utilities.auth import get_current_user

router = APIRouter()


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to check if user is admin"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create new user (admin only)"""
    # Check if username exists
    existing = await user_crud.get_user_by_username(db, user.username)
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")
    
    # Check if email exists
    existing = await user_crud.get_user_by_email(db, user.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already exists")
    
    # Create user
    new_user = await user_crud.create_user(db, user)
    return new_user


@router.get("/", response_model=list[UserResponse])
async def get_all_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get all users (admin only)"""
    users = await user_crud.get_all_users(db)
    return users

