"""
Permission decorators and middleware for FastAPI endpoints
"""
from functools import wraps
from typing import List, Optional, Union
from fastapi import HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.users.models import User


def require_permissions(permissions: Union[str, List[str]]):
    """
    Decorator to require specific permissions for an endpoint.
    
    Args:
        permissions: Single permission string or list of permissions
        
    Usage:
        @require_permissions("USER_VIEW")
        @require_permissions(["USER_VIEW", "USER_EDIT"])
    """
    if isinstance(permissions, str):
        permissions = [permissions]
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from dependencies
            current_user = None
            for key, value in kwargs.items():
                if isinstance(value, User):
                    current_user = value
                    break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check permissions
            for permission in permissions:
                if not current_user.has_permission(permission):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied: {permission} required"
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(role_name: str):
    """
    Decorator to require a specific role for an endpoint.
    
    Args:
        role_name: Name of the required role
        
    Usage:
        @require_role("ADMIN")
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from dependencies
            current_user = None
            for key, value in kwargs.items():
                if isinstance(value, User):
                    current_user = value
                    break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check role
            if not current_user.has_role(role_name):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role denied: {role_name} required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_superuser():
    """
    Decorator to require superuser status for an endpoint.
    
    Usage:
        @require_superuser()
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from dependencies
            current_user = None
            for key, value in kwargs.items():
                if isinstance(value, User):
                    current_user = value
                    break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check superuser status
            if not current_user.is_superuser:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Superuser access required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Dependency functions for use with FastAPI Depends
async def get_current_user_with_permissions(
    permissions: List[str],
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency function to get current user with required permissions.
    
    Args:
        permissions: List of required permissions
        current_user: Current authenticated user
        
    Returns:
        User if they have all required permissions
        
    Raises:
        HTTPException: If user doesn't have required permissions
    """
    for permission in permissions:
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission} required"
            )
    
    return current_user


async def get_current_user_with_role(
    role_name: str,
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency function to get current user with required role.
    
    Args:
        role_name: Required role name
        current_user: Current authenticated user
        
    Returns:
        User if they have the required role
        
    Raises:
        HTTPException: If user doesn't have required role
    """
    if not current_user.has_role(role_name):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role denied: {role_name} required"
        )
    
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency function to get current superuser.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User if they are a superuser
        
    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required"
        )
    
    return current_user


# Common permission dependency factories
def PermissionDependency(permission: str):
    """
    Factory function to create permission dependency.
    
    Args:
        permission: Required permission name
        
    Returns:
        Dependency function
        
    Usage:
        @app.get("/users/", dependencies=[Depends(PermissionDependency("USER_VIEW"))])
    """
    async def permission_dependency(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission} required"
            )
        return current_user
    
    return permission_dependency


def RoleDependency(role_name: str):
    """
    Factory function to create role dependency.
    
    Args:
        role_name: Required role name
        
    Returns:
        Dependency function
        
    Usage:
        @app.get("/admin/", dependencies=[Depends(RoleDependency("ADMIN"))])
    """
    async def role_dependency(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if not current_user.has_role(role_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role denied: {role_name} required"
            )
        return current_user
    
    return role_dependency


# Superuser dependency
SuperuserDependency = Depends(get_current_superuser)