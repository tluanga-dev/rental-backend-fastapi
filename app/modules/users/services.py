from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.orm import selectinload
from datetime import datetime
import json

from app.core.security import get_password_hash, verify_password
from app.shared.exceptions import NotFoundError, AlreadyExistsError, ValidationError
from app.modules.users.models import User, UserProfile, UserRole, UserRoleAssignment
from app.core.dependencies import PaginationParams


class UserService:
    """User service for managing users"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, user_data: Dict[str, Any]) -> User:
        """Create a new user"""
        # Check if user already exists by email
        if "email" in user_data:
            existing_user = await self.get_by_email(user_data["email"])
            if existing_user:
                raise AlreadyExistsError("User", "email", user_data["email"])
        
        # Check if user already exists by username
        if "username" in user_data:
            existing_user = await self.get_by_username(user_data["username"])
            if existing_user:
                raise AlreadyExistsError("User", "username", user_data["username"])
        
        # Hash password if provided
        if "password" in user_data:
            user_data["password"] = get_password_hash(user_data["password"])
        
        user = User(**user_data)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        stmt = select(User).where(User.username == username)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_username_or_email(self, identifier: str) -> Optional[User]:
        """Get user by username or email"""
        stmt = select(User).where(
            or_(User.username == identifier, User.email == identifier)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update(self, user_id: int, user_data: Dict[str, Any]) -> User:
        """Update user"""
        user = await self.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", user_id)
        
        # Check email uniqueness if email is being updated
        if "email" in user_data and user_data["email"] != user.email:
            existing_user = await self.get_by_email(user_data["email"])
            if existing_user:
                raise AlreadyExistsError("User", "email", user_data["email"])
        
        # Update fields
        for field, value in user_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def delete(self, user_id: int) -> bool:
        """Delete user"""
        user = await self.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", user_id)
        
        await self.db.delete(user)
        await self.db.commit()
        return True
    
    async def get_all(self, pagination: PaginationParams, search: Optional[str] = None) -> tuple[List[User], int]:
        """Get all users with pagination and search"""
        query = select(User)
        
        # Add search filter
        if search:
            search_filter = or_(
                User.email.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.execute(count_query)
        total = total.scalar()
        
        # Apply pagination
        query = query.offset(pagination.offset).limit(pagination.size)
        
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        return users, total
    
    async def update_last_login(self, user_id: int) -> None:
        """Update user's last login timestamp"""
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(last_login=datetime.utcnow())
        )
        await self.db.execute(stmt)
        await self.db.commit()
    
    async def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """Change user password"""
        user = await self.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", user_id)
        
        # Verify current password
        if not verify_password(current_password, user.password):
            raise ValidationError("Current password is incorrect")
        
        # Update password
        user.password = get_password_hash(new_password)
        await self.db.commit()
        return True
    
    async def update_status(self, user_id: int, is_active: Optional[bool] = None, is_verified: Optional[bool] = None) -> User:
        """Update user status"""
        user = await self.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", user_id)
        
        if is_active is not None:
            user.is_active = is_active
        
        if is_verified is not None:
            user.is_verified = is_verified
            if is_verified:
                user.email_verified_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(user)
        return user


class UserProfileService:
    """User profile service"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_or_update(self, user_id: int, profile_data: Dict[str, Any]) -> UserProfile:
        """Create or update user profile"""
        # Check if profile exists
        existing_profile = await self.get_by_user_id(user_id)
        
        if existing_profile:
            # Update existing profile
            for field, value in profile_data.items():
                if hasattr(existing_profile, field):
                    setattr(existing_profile, field, value)
            
            await self.db.commit()
            await self.db.refresh(existing_profile)
            return existing_profile
        else:
            # Create new profile
            profile_data["user_id"] = user_id
            profile = UserProfile(**profile_data)
            self.db.add(profile)
            await self.db.commit()
            await self.db.refresh(profile)
            return profile
    
    async def get_by_user_id(self, user_id: int) -> Optional[UserProfile]:
        """Get user profile by user ID"""
        stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def delete(self, user_id: int) -> bool:
        """Delete user profile"""
        profile = await self.get_by_user_id(user_id)
        if not profile:
            raise NotFoundError("UserProfile", user_id)
        
        await self.db.delete(profile)
        await self.db.commit()
        return True


class UserRoleService:
    """User role service for RBAC"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_role(self, role_data: Dict[str, Any]) -> UserRole:
        """Create a new role"""
        # Check if role already exists
        existing_role = await self.get_role_by_name(role_data["name"])
        if existing_role:
            raise AlreadyExistsError("Role", "name", role_data["name"])
        
        # Convert permissions list to JSON string
        if "permissions" in role_data:
            role_data["permissions"] = json.dumps(role_data["permissions"])
        
        role = UserRole(**role_data)
        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)
        return role
    
    async def get_role_by_id(self, role_id: int) -> Optional[UserRole]:
        """Get role by ID"""
        stmt = select(UserRole).where(UserRole.id == role_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_role_by_name(self, name: str) -> Optional[UserRole]:
        """Get role by name"""
        stmt = select(UserRole).where(UserRole.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all_roles(self, pagination: PaginationParams) -> tuple[List[UserRole], int]:
        """Get all roles with pagination"""
        query = select(UserRole)
        
        # Get total count
        count_query = select(func.count()).select_from(UserRole)
        total = await self.db.execute(count_query)
        total = total.scalar()
        
        # Apply pagination
        query = query.offset(pagination.offset).limit(pagination.size)
        
        result = await self.db.execute(query)
        roles = result.scalars().all()
        
        return roles, total
    
    async def assign_role(self, user_id: int, role_id: int, assigned_by: Optional[int] = None) -> UserRoleAssignment:
        """Assign role to user"""
        # Check if assignment already exists
        existing_assignment = await self.get_user_role_assignment(user_id, role_id)
        if existing_assignment:
            raise AlreadyExistsError("Role assignment", "user_id and role_id", f"{user_id},{role_id}")
        
        assignment = UserRoleAssignment(
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigned_by
        )
        
        self.db.add(assignment)
        await self.db.commit()
        await self.db.refresh(assignment)
        return assignment
    
    async def remove_role(self, user_id: int, role_id: int) -> bool:
        """Remove role from user"""
        assignment = await self.get_user_role_assignment(user_id, role_id)
        if not assignment:
            raise NotFoundError("Role assignment", f"user_id={user_id}, role_id={role_id}")
        
        await self.db.delete(assignment)
        await self.db.commit()
        return True
    
    async def get_user_role_assignment(self, user_id: int, role_id: int) -> Optional[UserRoleAssignment]:
        """Get user role assignment"""
        stmt = select(UserRoleAssignment).where(
            and_(
                UserRoleAssignment.user_id == user_id,
                UserRoleAssignment.role_id == role_id
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_roles(self, user_id: int) -> List[UserRole]:
        """Get all roles for a user"""
        stmt = (
            select(UserRole)
            .join(UserRoleAssignment)
            .where(UserRoleAssignment.user_id == user_id)
            .where(UserRole.is_active == True)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_user_permissions(self, user_id: int) -> List[str]:
        """Get all permissions for a user"""
        roles = await self.get_user_roles(user_id)
        permissions = set()
        
        for role in roles:
            if role.permissions:
                role_permissions = json.loads(role.permissions)
                permissions.update(role_permissions)
        
        return list(permissions)
    
    async def user_has_permission(self, user_id: int, permission: str) -> bool:
        """Check if user has specific permission"""
        permissions = await self.get_user_permissions(user_id)
        return permission in permissions