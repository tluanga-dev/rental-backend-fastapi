from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.security import verify_token, TokenData


# Security scheme
security = HTTPBearer()


# Authentication dependencies
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Get current authenticated user"""
    from app.modules.users.services import UserService
    from app.modules.users.models import User
    
    token = credentials.credentials
    token_data = verify_token(token, "access")
    
    user_service = UserService(db)
    user = await user_service.get_by_id(token_data.user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user = Depends(get_current_user)
):
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_superuser(
    current_user = Depends(get_current_user)
):
    """Get current superuser"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


# Optional authentication dependency
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Get current user if authenticated, otherwise None"""
    from app.modules.users.services import UserService
    
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        token_data = verify_token(token, "access")
        
        user_service = UserService(db)
        user = await user_service.get_by_id(token_data.user_id)
        
        if user and user.is_active:
            return user
    except Exception:
        pass
    
    return None


# Pagination dependency
class PaginationParams:
    def __init__(self, page: int = 1, size: int = 20):
        self.page = max(1, page)
        self.size = min(100, max(1, size))
        self.offset = (self.page - 1) * self.size


def get_pagination_params(page: int = 1, size: int = 20) -> PaginationParams:
    """Get pagination parameters"""
    return PaginationParams(page=page, size=size)