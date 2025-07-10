from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_
from fastapi import HTTPException, status, Request
import secrets
import uuid

from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_token_pair,
    verify_token,
    create_access_token
)
from app.core.config import settings
from app.shared.exceptions import (
    InvalidCredentialsError,
    NotFoundError,
    AlreadyExistsError,
    ValidationError
)
from app.modules.auth.models import RefreshToken, LoginAttempt, PasswordResetToken
from app.modules.users.models import User
from app.modules.users.services import UserService


class AuthService:
    """Authentication service"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_service = UserService(db)
    
    async def register(self, username: str, email: str, password: str, full_name: str) -> User:
        """Register a new user"""
        # Check if user already exists
        existing_user = await self.user_service.get_by_email(email)
        if existing_user:
            raise AlreadyExistsError("User", "email", email)
        
        # Check if username already exists
        existing_username = await self.user_service.get_by_username(username)
        if existing_username:
            raise AlreadyExistsError("User", "username", username)
        
        # Validate password
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            raise ValidationError(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long")
        
        # Create user
        user_data = {
            "username": username,
            "email": email,
            "password": password,  # UserService will hash this
            "full_name": full_name,
            "is_active": True
        }
        
        user = await self.user_service.create(user_data)
        return user
    
    async def login(self, username_or_email: str, password: str, request: Request = None) -> Dict[str, Any]:
        """Authenticate user and return tokens"""
        # Get client info
        ip_address = request.client.host if request else None
        user_agent = request.headers.get("user-agent") if request else None
        
        # Get user by username or email
        user = await self.user_service.get_by_username_or_email(username_or_email)
        
        # Log login attempt
        await self._log_login_attempt(
            email=username_or_email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False
        )
        
        if not user:
            raise InvalidCredentialsError("Invalid username/email or password")
        
        if not user.is_active:
            raise InvalidCredentialsError("Account is disabled")
        
        # Verify password
        if not verify_password(password, user.password):
            raise InvalidCredentialsError("Invalid username/email or password")
        
        # Create tokens
        tokens = create_token_pair(
            user_id=user.id,
            username=user.username,  # Use username instead of email
            scopes=["read", "write"] if user.is_active else ["read"]
        )
        
        # Store refresh token
        await self._store_refresh_token(
            user_id=user.id,
            token=tokens.refresh_token,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Update successful login attempt
        await self._log_login_attempt(
            email=username_or_email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )
        
        # Update last login
        await self.user_service.update_last_login(user.id)
        
        return {
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "token_type": tokens.token_type,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser
            }
        }
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        # Verify refresh token
        token_data = verify_token(refresh_token, "refresh")
        
        # Check if refresh token exists in database
        stmt = select(RefreshToken).where(
            and_(
                RefreshToken.token == refresh_token,
                RefreshToken.is_active == True,
                RefreshToken.expires_at > datetime.utcnow()
            )
        )
        result = await self.db.execute(stmt)
        stored_token = result.scalar_one_or_none()
        
        if not stored_token:
            raise InvalidCredentialsError("Invalid refresh token")
        
        # Get user
        user = await self.user_service.get_by_id(token_data.user_id)
        if not user or not user.is_active:
            raise InvalidCredentialsError("User not found or inactive")
        
        # Create new access token
        access_token = create_access_token({
            "sub": user.email,
            "user_id": user.id,
            "scopes": ["read", "write"] if user.is_active else ["read"]
        })
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    async def logout(self, refresh_token: str) -> None:
        """Logout user by invalidating refresh token"""
        stmt = select(RefreshToken).where(RefreshToken.token == refresh_token)
        result = await self.db.execute(stmt)
        stored_token = result.scalar_one_or_none()
        
        if stored_token:
            stored_token.is_active = False
            await self.db.commit()
    
    async def logout_all(self, user_id: int) -> None:
        """Logout user from all devices"""
        stmt = (
            select(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .where(RefreshToken.is_active == True)
        )
        result = await self.db.execute(stmt)
        tokens = result.scalars().all()
        
        for token in tokens:
            token.is_active = False
        
        await self.db.commit()
    
    async def change_password(self, user_id: int, current_password: str, new_password: str) -> None:
        """Change user password"""
        user = await self.user_service.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", user_id)
        
        # Verify current password
        if not verify_password(current_password, user.password):
            raise InvalidCredentialsError("Current password is incorrect")
        
        # Validate new password
        if len(new_password) < settings.PASSWORD_MIN_LENGTH:
            raise ValidationError(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long")
        
        # Update password
        user.password = get_password_hash(new_password)
        await self.db.commit()
        
        # Logout from all devices for security
        await self.logout_all(user_id)
    
    async def forgot_password(self, email: str) -> str:
        """Generate password reset token"""
        user = await self.user_service.get_by_email(email)
        if not user:
            # Don't reveal if email exists
            return "If the email exists, a reset link will be sent"
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
        
        # Store reset token
        password_reset = PasswordResetToken(
            token=reset_token,
            user_id=user.id,
            expires_at=expires_at
        )
        
        self.db.add(password_reset)
        await self.db.commit()
        
        # In production, send email here
        return reset_token
    
    async def reset_password(self, token: str, new_password: str) -> None:
        """Reset password using reset token"""
        # Find valid reset token
        stmt = select(PasswordResetToken).where(
            and_(
                PasswordResetToken.token == token,
                PasswordResetToken.is_used == False,
                PasswordResetToken.expires_at > datetime.utcnow()
            )
        )
        result = await self.db.execute(stmt)
        reset_token = result.scalar_one_or_none()
        
        if not reset_token:
            raise InvalidCredentialsError("Invalid or expired reset token")
        
        # Get user
        user = await self.user_service.get_by_id(reset_token.user_id)
        if not user:
            raise NotFoundError("User", reset_token.user_id)
        
        # Validate new password
        if len(new_password) < settings.PASSWORD_MIN_LENGTH:
            raise ValidationError(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long")
        
        # Update password
        user.password = get_password_hash(new_password)
        reset_token.is_used = True
        
        await self.db.commit()
        
        # Logout from all devices for security
        await self.logout_all(user.id)
    
    async def _store_refresh_token(
        self, 
        user_id: int, 
        token: str, 
        ip_address: str = None,
        user_agent: str = None
    ) -> None:
        """Store refresh token in database"""
        expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        refresh_token = RefreshToken(
            token=token,
            user_id=user_id,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(refresh_token)
        await self.db.commit()
    
    async def _log_login_attempt(
        self,
        email: str,
        ip_address: str = None,
        user_agent: str = None,
        success: bool = False,
        failure_reason: str = None
    ) -> None:
        """Log login attempt for security tracking"""
        login_attempt = LoginAttempt(
            email=email,
            ip_address=ip_address or "unknown",
            user_agent=user_agent,
            success=success,
            failure_reason=failure_reason
        )
        
        self.db.add(login_attempt)
        await self.db.commit()
    
    async def cleanup_expired_tokens(self) -> None:
        """Clean up expired refresh tokens and reset tokens"""
        now = datetime.utcnow()
        
        # Delete expired refresh tokens
        await self.db.execute(
            delete(RefreshToken).where(RefreshToken.expires_at < now)
        )
        
        # Delete expired reset tokens
        await self.db.execute(
            delete(PasswordResetToken).where(PasswordResetToken.expires_at < now)
        )
        
        await self.db.commit()