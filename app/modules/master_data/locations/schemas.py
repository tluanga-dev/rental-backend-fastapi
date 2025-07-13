from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


class LocationCreate(BaseModel):
    """Schema for creating a new location."""
    location_code: str = Field(..., max_length=20, description="Unique location code")
    location_name: str = Field(..., max_length=100, description="Location name")
    location_type: str = Field(..., max_length=20, description="Location type")
    address: str = Field(..., description="Street address")
    city: str = Field(..., max_length=100, description="City")
    state: str = Field(..., max_length=100, description="State")
    country: str = Field(..., max_length=100, description="Country")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal code")
    contact_number: Optional[str] = Field(None, max_length=20, description="Contact number")
    email: Optional[str] = Field(None, max_length=255, description="Email address")
    manager_user_id: Optional[UUID] = Field(None, description="Manager user ID")


class LocationUpdate(BaseModel):
    """Schema for updating a location."""
    location_name: Optional[str] = Field(None, max_length=100, description="Location name")
    location_type: Optional[str] = Field(None, max_length=20, description="Location type")
    address: Optional[str] = Field(None, description="Street address")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=100, description="State")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal code")
    contact_number: Optional[str] = Field(None, max_length=20, description="Contact number")
    email: Optional[str] = Field(None, max_length=255, description="Email address")
    manager_user_id: Optional[UUID] = Field(None, description="Manager user ID")


class LocationResponse(BaseModel):
    """Schema for location response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    location_code: str
    location_name: str
    location_type: str
    address: Optional[str] = None
    city: str
    state: str
    country: str
    postal_code: Optional[str] = None
    contact_number: Optional[str] = None
    email: Optional[str] = None
    manager_user_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool