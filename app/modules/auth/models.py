from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, Index, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, List
from enum import Enum

from app.db.base import Base


class RefreshToken(Base):
    """Refresh token model for JWT authentication"""
    __tablename__ = "refresh_tokens"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    token: Mapped[str] = mapped_column(String(500), unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Device/client information
    device_info: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # IPv6 support
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="refresh_tokens")
    
    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, active={self.is_active})>"


class LoginAttempt(Base):
    """Login attempt tracking for security"""
    __tablename__ = "login_attempts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    
    # Additional security fields
    failure_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    def __repr__(self):
        return f"<LoginAttempt(id={self.id}, email={self.email}, success={self.success})>"


class PasswordResetToken(Base):
    """Password reset token model"""
    __tablename__ = "password_reset_tokens"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="password_reset_tokens")
    
    def __repr__(self):
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id}, used={self.is_used})>"


class UserType(str, Enum):
    """User type enumeration for hierarchy"""
    SUPERADMIN = "SUPERADMIN"
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    USER = "USER"
    CUSTOMER = "CUSTOMER"


class PermissionRiskLevel(str, Enum):
    """Permission risk level enumeration"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# Association tables for many-to-many relationships
role_permissions_table = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True),
    Index('idx_role_permissions_role', 'role_id'),
    Index('idx_role_permissions_permission', 'permission_id'),
)

user_roles_table = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Index('idx_user_roles_user', 'user_id'),
    Index('idx_user_roles_role', 'role_id'),
)

user_permissions_table = Table(
    'user_permissions',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True),
    Column('granted_by', Integer, ForeignKey('users.id'), nullable=True),
    Column('granted_at', DateTime, nullable=False, default=func.now()),
    Column('expires_at', DateTime, nullable=True),
    Index('idx_user_permissions_user', 'user_id'),
    Index('idx_user_permissions_permission', 'permission_id'),
)


class Role(Base):
    """Role model for RBAC"""
    __tablename__ = "roles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_system_role: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    permissions = relationship("Permission", secondary=role_permissions_table, back_populates="roles")
    users = relationship("User", secondary=user_roles_table, back_populates="roles")
    
    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name})>"
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if role has a specific permission"""
        return any(perm.name == permission_name for perm in self.permissions)
    
    def get_permissions(self) -> List[str]:
        """Get all permission names for this role"""
        return [perm.name for perm in self.permissions]


class Permission(Base):
    """Permission model for fine-grained access control"""
    __tablename__ = "permissions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resource: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), default=PermissionRiskLevel.LOW.value, nullable=False)
    is_system_permission: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    roles = relationship("Role", secondary=role_permissions_table, back_populates="permissions")
    
    def __repr__(self):
        return f"<Permission(id={self.id}, name={self.name}, resource={self.resource}, action={self.action})>"
    
    def get_risk_level(self) -> PermissionRiskLevel:
        """Get risk level enum"""
        return PermissionRiskLevel(self.risk_level)
