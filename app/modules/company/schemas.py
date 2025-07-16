from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from uuid import UUID


class CompanyBase(BaseModel):
    """Base company schema with common fields."""
    
    company_name: str = Field(..., min_length=1, max_length=255, description="Company name")
    address: Optional[str] = Field(None, description="Company address")
    email: Optional[str] = Field(None, max_length=255, description="Company email")
    phone: Optional[str] = Field(None, max_length=50, description="Company phone number")
    gst_no: Optional[str] = Field(None, max_length=50, description="GST registration number")
    registration_number: Optional[str] = Field(None, max_length=100, description="Company registration number")
    
    @field_validator('company_name')
    @classmethod
    def validate_company_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Company name cannot be empty')
        return v.strip()
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('Email cannot be empty if provided')
            
            # Basic email validation
            if "@" not in v or "." not in v.split("@")[-1]:
                raise ValueError('Invalid email format')
            
            return v.strip().lower()
        return v
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('Phone cannot be empty if provided')
            return v.strip()
        return v
    
    @field_validator('gst_no')
    @classmethod
    def validate_gst_no(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('GST number cannot be empty if provided')
            return v.upper().strip()
        return v
    
    @field_validator('registration_number')
    @classmethod
    def validate_registration_number(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('Registration number cannot be empty if provided')
            return v.upper().strip()
        return v
    
    @field_validator('address')
    @classmethod
    def validate_address(cls, v):
        if v is not None:
            return v.strip() if v.strip() else None
        return v


class CompanyCreate(CompanyBase):
    """Schema for creating a new company."""
    pass


class CompanyUpdate(BaseModel):
    """Schema for updating an existing company."""
    
    company_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Company name")
    address: Optional[str] = Field(None, description="Company address")
    email: Optional[str] = Field(None, max_length=255, description="Company email")
    phone: Optional[str] = Field(None, max_length=50, description="Company phone number")
    gst_no: Optional[str] = Field(None, max_length=50, description="GST registration number")
    registration_number: Optional[str] = Field(None, max_length=100, description="Company registration number")
    is_active: Optional[bool] = Field(None, description="Company active status")
    
    @field_validator('company_name')
    @classmethod
    def validate_company_name(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Company name cannot be empty')
            return v.strip()
        return v
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('Email cannot be empty if provided')
            
            # Basic email validation
            if "@" not in v or "." not in v.split("@")[-1]:
                raise ValueError('Invalid email format')
            
            return v.strip().lower()
        return v
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('Phone cannot be empty if provided')
            return v.strip()
        return v
    
    @field_validator('gst_no')
    @classmethod
    def validate_gst_no(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('GST number cannot be empty if provided')
            return v.upper().strip()
        return v
    
    @field_validator('registration_number')
    @classmethod
    def validate_registration_number(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('Registration number cannot be empty if provided')
            return v.upper().strip()
        return v
    
    @field_validator('address')
    @classmethod
    def validate_address(cls, v):
        if v is not None:
            return v.strip() if v.strip() else None
        return v


class CompanyResponse(CompanyBase):
    """Schema for company response with all fields."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Company unique identifier")
    is_active: bool = Field(True, description="Company active status")
    created_at: datetime = Field(..., description="Company creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Company last update timestamp")
    created_by: Optional[str] = Field(None, description="User who created the company")
    updated_by: Optional[str] = Field(None, description="User who last updated the company")


class CompanySummary(BaseModel):
    """Schema for company summary with minimal fields."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Company unique identifier")
    company_name: str = Field(..., description="Company name")
    email: Optional[str] = Field(None, description="Company email")
    phone: Optional[str] = Field(None, description="Company phone")
    is_active: bool = Field(True, description="Company active status")


class CompanyList(BaseModel):
    """Schema for paginated company list response."""
    
    items: list[CompanySummary] = Field(..., description="List of company summaries")
    total: int = Field(..., description="Total number of companies")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")


class CompanyFilter(BaseModel):
    """Schema for company filtering and search."""
    
    company_name: Optional[str] = Field(None, description="Filter by company name (partial match)")
    email: Optional[str] = Field(None, description="Filter by email (partial match)")
    gst_no: Optional[str] = Field(None, description="Filter by GST number (partial match)")
    registration_number: Optional[str] = Field(None, description="Filter by registration number (partial match)")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    search: Optional[str] = Field(None, description="Search in name, email, GST and registration number")
    
    @field_validator('company_name', 'email', 'gst_no', 'registration_number', 'search')
    @classmethod
    def validate_string_filters(cls, v):
        if v is not None:
            return v.strip() if v.strip() else None
        return v


class CompanySort(BaseModel):
    """Schema for company sorting options."""
    
    field: str = Field('company_name', description="Field to sort by")
    direction: str = Field('asc', description="Sort direction (asc/desc)")
    
    @field_validator('field')
    @classmethod
    def validate_field(cls, v):
        allowed_fields = ['company_name', 'email', 'created_at', 'updated_at', 'is_active']
        if v not in allowed_fields:
            raise ValueError(f'Sort field must be one of: {", ".join(allowed_fields)}')
        return v
    
    @field_validator('direction')
    @classmethod
    def validate_direction(cls, v):
        if v.lower() not in ['asc', 'desc']:
            raise ValueError('Sort direction must be "asc" or "desc"')
        return v.lower()


class CompanyActiveStatus(BaseModel):
    """Schema for activating/deactivating a company."""
    
    is_active: bool = Field(..., description="Active status to set")