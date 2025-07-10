from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    bio: Optional[str] = Field(None, max_length=1000)
    
    model_config = {"from_attributes": True}


class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(..., min_length=8)
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class UserUpdate(BaseModel):
    """User update schema"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    bio: Optional[str] = Field(None, max_length=1000)
    avatar_url: Optional[str] = Field(None, max_length=500)
    
    model_config = {"from_attributes": True}


class UserResponse(UserBase):
    """User response schema"""
    id: int
    is_active: bool
    is_superuser: bool
    is_verified: bool
    avatar_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    email_verified_at: Optional[datetime]
    
    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """User list response schema"""
    id: int
    email: str
    full_name: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    last_login: Optional[datetime]
    
    model_config = {"from_attributes": True}


class UserProfileBase(BaseModel):
    """Base user profile schema"""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = Field(None, max_length=10)
    
    # Address
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    
    # Social links
    website: Optional[str] = Field(None, max_length=500)
    linkedin: Optional[str] = Field(None, max_length=500)
    twitter: Optional[str] = Field(None, max_length=500)
    github: Optional[str] = Field(None, max_length=500)
    
    # Preferences
    timezone: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=10)
    theme: Optional[str] = Field(None, max_length=20)
    
    # Notification preferences
    email_notifications: bool = True
    sms_notifications: bool = False
    push_notifications: bool = True
    
    model_config = {"from_attributes": True}


class UserProfileCreate(UserProfileBase):
    """User profile creation schema"""
    pass


class UserProfileUpdate(UserProfileBase):
    """User profile update schema"""
    pass


class UserProfileResponse(UserProfileBase):
    """User profile response schema"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class UserRoleBase(BaseModel):
    """Base user role schema"""
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    is_active: bool = True
    
    model_config = {"from_attributes": True}


class UserRoleCreate(UserRoleBase):
    """User role creation schema"""
    permissions: Optional[List[str]] = []


class UserRoleUpdate(BaseModel):
    """User role update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    permissions: Optional[List[str]] = None
    
    model_config = {"from_attributes": True}


class UserRoleResponse(UserRoleBase):
    """User role response schema"""
    id: int
    permissions: List[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class UserRoleAssignmentBase(BaseModel):
    """Base user role assignment schema"""
    user_id: int
    role_id: int
    
    model_config = {"from_attributes": True}


class UserRoleAssignmentCreate(UserRoleAssignmentBase):
    """User role assignment creation schema"""
    pass


class UserRoleAssignmentResponse(UserRoleAssignmentBase):
    """User role assignment response schema"""
    id: int
    assigned_at: datetime
    assigned_by: Optional[int]
    
    model_config = {"from_attributes": True}


class UserWithRoles(UserResponse):
    """User with roles schema"""
    roles: List[UserRoleResponse] = []
    
    model_config = {"from_attributes": True}


class UserWithProfile(UserResponse):
    """User with profile schema"""
    profile: Optional[UserProfileResponse] = None
    
    model_config = {"from_attributes": True}


class PasswordChangeRequest(BaseModel):
    """Password change request schema"""
    current_password: str
    new_password: str = Field(..., min_length=8)
    
    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class UserStatusUpdate(BaseModel):
    """User status update schema"""
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    
    model_config = {"from_attributes": True}