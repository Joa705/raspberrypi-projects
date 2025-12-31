"""
Authentication utilities for password hashing and JWT tokens.
"""
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from typing import Optional

# Project imports
from database.db import get_db
from config import settings

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_HOURS = settings.access_token_expire_hours

# HTTP Bearer security
security = HTTPBearer()


def get_password_hash(password: str) -> str:
    """Hash a plain text password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    
    # Convert user_id to string if it's the "sub" claim
    if "sub" in to_encode and isinstance(to_encode["sub"], int):
        to_encode["sub"] = str(to_encode["sub"])
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """FastAPI dependency to get current authenticated user."""
    import crud.user as user_crud
    
    # Decode token (pure, testable)
    user_id = _decode_access_token(credentials.credentials)
    
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Get user (separated CRUD operation)
    user = await user_crud.get_user_by_id(db, user_id)
    
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    return user



# Internal functions #
def _decode_access_token(token: str) -> Optional[int]:
    """Decode JWT token and return user_id. Returns None if invalid."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            logger.error("No 'sub' claim in token")
            return None
        
        # Convert string back to int
        user_id = int(user_id_str)
        return user_id
    except (JWTError, ValueError) as e:
        logger.error(f"JWT decode error: {e}")
        return None