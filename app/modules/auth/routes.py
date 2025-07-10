from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.services import AuthService
from app.modules.auth.schemas import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    LogoutResponse
)
from app.modules.auth.dependencies import get_current_user, get_auth_service
from app.modules.users.models import User
from app.shared.models import BaseResponse


router = APIRouter()


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user"""
    user = await auth_service.register(
        email=request.email,
        password=request.password,
        full_name=request.full_name
    )
    
    return RegisterResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    http_request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Login user and return tokens"""
    result = await auth_service.login(
        username_or_email=request.username,
        password=request.password,
        request=http_request
    )
    
    return LoginResponse(**result)


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Refresh access token using refresh token"""
    result = await auth_service.refresh_token(request.refresh_token)
    
    return RefreshTokenResponse(**result)


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Logout user by invalidating refresh token"""
    await auth_service.logout(request.refresh_token)
    
    return LogoutResponse()


@router.post("/logout-all", response_model=LogoutResponse)
async def logout_all(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Logout user from all devices"""
    await auth_service.logout_all(current_user.id)
    
    return LogoutResponse(message="Successfully logged out from all devices")


@router.post("/change-password", response_model=BaseResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Change user password"""
    await auth_service.change_password(
        user_id=current_user.id,
        current_password=request.current_password,
        new_password=request.new_password
    )
    
    return BaseResponse(message="Password changed successfully")


@router.post("/forgot-password", response_model=BaseResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Request password reset token"""
    await auth_service.forgot_password(request.email)
    
    return BaseResponse(message="If the email exists, a reset link will be sent")


@router.post("/reset-password", response_model=BaseResponse)
async def reset_password(
    request: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Reset password using reset token"""
    await auth_service.reset_password(request.token, request.new_password)
    
    return BaseResponse(message="Password reset successfully")


@router.get("/me", response_model=dict)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "is_superuser": current_user.is_superuser,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at,
        "last_login": current_user.last_login
    }