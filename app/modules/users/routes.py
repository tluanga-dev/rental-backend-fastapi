from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.core.database import get_db
from app.core.dependencies import get_pagination_params, PaginationParams
from app.modules.auth.dependencies import get_current_user, get_current_superuser
from app.modules.users.models import User
from app.modules.users.services import UserService, UserProfileService, UserRoleService
from app.modules.users.schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileResponse,
    UserRoleCreate,
    UserRoleUpdate,
    UserRoleResponse,
    UserRoleAssignmentCreate,
    UserRoleAssignmentResponse,
    UserWithRoles,
    UserWithProfile,
    PasswordChangeRequest,
    UserStatusUpdate
)
from app.shared.models import BaseResponse, PaginatedResponse


router = APIRouter()


# User management endpoints
@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user profile"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user profile"""
    user_service = UserService(db)
    
    # Convert to dict and remove None values
    update_data = user_update.dict(exclude_unset=True)
    
    updated_user = await user_service.update(current_user.id, update_data)
    return updated_user


@router.post("/me/change-password", response_model=BaseResponse)
async def change_current_user_password(
    password_change: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change current user password"""
    user_service = UserService(db)
    
    await user_service.change_password(
        current_user.id,
        password_change.current_password,
        password_change.new_password
    )
    
    return BaseResponse(message="Password changed successfully")


# User profile endpoints
@router.get("/me/profile", response_model=UserProfileResponse)
async def get_current_user_extended_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user extended profile"""
    profile_service = UserProfileService(db)
    profile = await profile_service.get_by_user_id(current_user.id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return profile


@router.put("/me/profile", response_model=UserProfileResponse)
async def update_current_user_extended_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user extended profile"""
    profile_service = UserProfileService(db)
    
    # Convert to dict and remove None values
    update_data = profile_update.dict(exclude_unset=True)
    
    profile = await profile_service.create_or_update(current_user.id, update_data)
    return profile


# Admin endpoints for user management
@router.get("/", response_model=PaginatedResponse[UserListResponse])
async def get_users(
    pagination: PaginationParams = Depends(get_pagination_params),
    search: Optional[str] = Query(None, description="Search users by email or name"),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """Get all users (admin only)"""
    user_service = UserService(db)
    
    users, total = await user_service.get_all(pagination, search)
    
    return PaginatedResponse(
        data=[UserListResponse.from_orm(user) for user in users],
        page=pagination.page,
        size=pagination.size,
        total=total,
        pages=(total + pagination.size - 1) // pagination.size
    )


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_create: UserCreate,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user (admin only)"""
    user_service = UserService(db)
    
    user_data = user_create.dict()
    user = await user_service.create(user_data)
    
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """Get user by ID (admin only)"""
    user_service = UserService(db)
    
    user = await user_service.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """Update user (admin only)"""
    user_service = UserService(db)
    
    # Convert to dict and remove None values
    update_data = user_update.dict(exclude_unset=True)
    
    updated_user = await user_service.update(user_id, update_data)
    return updated_user


@router.patch("/{user_id}/status", response_model=UserResponse)
async def update_user_status(
    user_id: int,
    status_update: UserStatusUpdate,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """Update user status (admin only)"""
    user_service = UserService(db)
    
    updated_user = await user_service.update_status(
        user_id,
        status_update.is_active,
        status_update.is_verified
    )
    return updated_user


@router.delete("/{user_id}", response_model=BaseResponse)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """Delete user (admin only)"""
    user_service = UserService(db)
    
    await user_service.delete(user_id)
    return BaseResponse(message="User deleted successfully")


# Role management endpoints
@router.get("/roles/", response_model=PaginatedResponse[UserRoleResponse])
async def get_roles(
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """Get all roles (admin only)"""
    role_service = UserRoleService(db)
    
    roles, total = await role_service.get_all_roles(pagination)
    
    # Convert permissions from JSON string to list
    role_responses = []
    for role in roles:
        role_dict = {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "is_active": role.is_active,
            "permissions": role.permissions.split(",") if role.permissions else [],
            "created_at": role.created_at,
            "updated_at": role.updated_at
        }
        role_responses.append(UserRoleResponse(**role_dict))
    
    return PaginatedResponse(
        data=role_responses,
        page=pagination.page,
        size=pagination.size,
        total=total,
        pages=(total + pagination.size - 1) // pagination.size
    )


@router.post("/roles/", response_model=UserRoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_create: UserRoleCreate,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """Create a new role (admin only)"""
    role_service = UserRoleService(db)
    
    role_data = role_create.dict()
    role = await role_service.create_role(role_data)
    
    return UserRoleResponse(
        id=role.id,
        name=role.name,
        description=role.description,
        is_active=role.is_active,
        permissions=role.permissions.split(",") if role.permissions else [],
        created_at=role.created_at,
        updated_at=role.updated_at
    )


@router.post("/{user_id}/roles/{role_id}", response_model=UserRoleAssignmentResponse)
async def assign_role_to_user(
    user_id: int,
    role_id: int,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """Assign role to user (admin only)"""
    role_service = UserRoleService(db)
    
    assignment = await role_service.assign_role(user_id, role_id, current_user.id)
    return assignment


@router.delete("/{user_id}/roles/{role_id}", response_model=BaseResponse)
async def remove_role_from_user(
    user_id: int,
    role_id: int,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """Remove role from user (admin only)"""
    role_service = UserRoleService(db)
    
    await role_service.remove_role(user_id, role_id)
    return BaseResponse(message="Role removed from user successfully")


@router.get("/{user_id}/roles", response_model=List[UserRoleResponse])
async def get_user_roles(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """Get user roles (admin only)"""
    role_service = UserRoleService(db)
    
    roles = await role_service.get_user_roles(user_id)
    
    # Convert permissions from JSON string to list
    role_responses = []
    for role in roles:
        role_dict = {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "is_active": role.is_active,
            "permissions": role.permissions.split(",") if role.permissions else [],
            "created_at": role.created_at,
            "updated_at": role.updated_at
        }
        role_responses.append(UserRoleResponse(**role_dict))
    
    return role_responses


@router.get("/{user_id}/permissions", response_model=List[str])
async def get_user_permissions(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """Get user permissions (admin only)"""
    role_service = UserRoleService(db)
    
    permissions = await role_service.get_user_permissions(user_id)
    return permissions