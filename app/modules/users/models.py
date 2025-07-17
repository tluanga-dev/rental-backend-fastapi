from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, List

from app.db.base import Base
from app.modules.auth.models import user_roles_table, user_permissions_table, UserType, Role, Permission

# Create UserRole alias for backward compatibility
UserRole = Role


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Enhanced name fields for frontend compatibility
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Status fields
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # User type for hierarchy
    user_type: Mapped[str] = mapped_column(String(20), default=UserType.USER.value, nullable=False)
    
    # Optional profile fields
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    
    # RBAC relationships
    roles = relationship("Role", secondary=user_roles_table, back_populates="users")
    direct_permissions = relationship("Permission", secondary=user_permissions_table, 
                                    primaryjoin="User.id == user_permissions.c.user_id",
                                    secondaryjoin="Permission.id == user_permissions.c.permission_id")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, active={self.is_active})>"
    
    @property
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.is_active
    
    @property
    def display_name(self) -> str:
        """Get display name for user"""
        return self.full_name or self.email
    
    @property
    def name(self) -> str:
        """Get name for frontend compatibility"""
        return self.full_name or f"{self.first_name or ''} {self.last_name or ''}".strip() or self.email
    
    @property
    def firstName(self) -> str:
        """Get first name for frontend compatibility"""
        return self.first_name or ""
    
    @property
    def lastName(self) -> str:
        """Get last name for frontend compatibility"""
        return self.last_name or ""
    
    def get_user_type(self) -> UserType:
        """Get user type enum"""
        return UserType(self.user_type)
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role"""
        return any(role.name == role_name for role in self.roles)
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if user has a specific permission"""
        # Superusers have all permissions
        if self.is_superuser:
            return True
            
        # Check direct permissions
        for permission in self.direct_permissions:
            if permission.name == permission_name:
                return True
                
        # Check role permissions
        for role in self.roles:
            if role.has_permission(permission_name):
                return True
        return False
    
    def get_permissions(self) -> List[str]:
        """Get all permissions for the user"""
        permissions = set()
        
        # Add direct permissions
        for permission in self.direct_permissions:
            permissions.add(permission.name)
            
        # Add role permissions
        for role in self.roles:
            permissions.update(role.get_permissions())
            
        return list(permissions)
    
    def get_role_permissions(self) -> List[str]:
        """Get all permissions from roles"""
        permissions = set()
        for role in self.roles:
            permissions.update(role.get_permissions())
        return list(permissions)
    
    def get_direct_permissions(self) -> List[str]:
        """Get all direct permissions for the user"""
        return [perm.name for perm in self.direct_permissions]
    
    def get_effective_permissions(self) -> dict:
        """Get effective permissions structure expected by frontend"""
        all_permissions = self.get_permissions()
        role_permissions = self.get_role_permissions()
        direct_permissions = self.get_direct_permissions()
        
        return {
            "userType": self.user_type,
            "isSuperuser": self.is_superuser,
            "rolePermissions": role_permissions,
            "directPermissions": direct_permissions,
            "allPermissions": all_permissions,
            "all_permissions": all_permissions,  # Snake_case fallback
        }


class UserProfile(Base):
    """Extended user profile model"""
    __tablename__ = "user_profiles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    
    # Extended profile fields
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    date_of_birth: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    # Address information
    address_line1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Social links
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    linkedin: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    twitter: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    github: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Preferences
    timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    theme: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Notification preferences
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sms_notifications: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    push_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    def __repr__(self):
        return f"<UserProfile(id={self.id}, user_id={self.user_id})>"
