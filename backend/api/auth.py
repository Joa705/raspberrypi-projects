from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
import crud.user as user_crud
from utilities.auth import verify_password, create_access_token
from schemas.auth import TokenResponse

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Login with username and password.
    Returns JWT access token.
    """
    # Get user by username
    user = await user_crud.get_user_by_username(db, form_data.username)
    
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    # Verify password
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")
    
    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "is_admin": user.is_admin
    }