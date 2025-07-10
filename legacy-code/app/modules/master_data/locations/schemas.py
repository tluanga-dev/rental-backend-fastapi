from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


class LocationCreate(BaseModel):
    """Schema for creating a new location."""
    location_code: str = Field(..., max_length=20, description="Unique location code")
    location_name: str = Field(..., max_length=100, description="Location name")
    location_type: str = Field(..., max_length=20, description="Location type")
    address_line1: str = Field(..., max_length=200, description="Address line 1")
    address_line2: Optional[str] = Field(None, max_length=200, description="Address line 2")
    city: str = Field(..., max_length=100, description="City")
    state: str = Field(..., max_length=100, description="State")
    postal_code: str = Field(..., max_length=20, description="Postal code")
    country: str = Field(..., max_length=100, description="Country")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    email: Optional[str] = Field(None, max_length=200, description="Email address")
    manager_user_id: Optional[UUID] = Field(None, description="Manager user ID")
    operating_hours: Optional[str] = Field(None, description="Operating hours")
    capacity: Optional[int] = Field(None, ge=0, description="Storage capacity")
    description: Optional[str] = Field(None, description="Location description")


class LocationUpdate(BaseModel):
    """Schema for updating a location."""
    location_name: Optional[str] = Field(None, max_length=100, description="Location name")
    location_type: Optional[str] = Field(None, max_length=20, description="Location type")
    address_line1: Optional[str] = Field(None, max_length=200, description="Address line 1")
    address_line2: Optional[str] = Field(None, max_length=200, description="Address line 2")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=100, description="State")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal code")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    email: Optional[str] = Field(None, max_length=200, description="Email address")
    manager_user_id: Optional[UUID] = Field(None, description="Manager user ID")
    operating_hours: Optional[str] = Field(None, description="Operating hours")
    capacity: Optional[int] = Field(None, ge=0, description="Storage capacity")
    description: Optional[str] = Field(None, description="Location description")


class LocationResponse(BaseModel):
    """Schema for location response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    location_code: str
    location_name: str
    location_type: str
    address_line1: str
    address_line2: Optional[str]
    city: str
    state: str
    postal_code: str
    country: str
    phone: Optional[str]
    email: Optional[str]
    manager_user_id: Optional[UUID]
    operating_hours: Optional[str]
    capacity: Optional[int]
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_active: bool