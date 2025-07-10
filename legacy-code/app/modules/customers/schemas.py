from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from uuid import UUID

from app.modules.customers.models import CustomerType, CustomerStatus, BlacklistStatus, CreditRating


class CustomerCreate(BaseModel):
    """Schema for creating a new customer."""
    customer_code: str = Field(..., max_length=50, description="Unique customer code")
    customer_type: CustomerType = Field(..., description="Customer type")
    company_name: Optional[str] = Field(None, max_length=200, description="Company name")
    first_name: str = Field(..., max_length=100, description="First name")
    last_name: str = Field(..., max_length=100, description="Last name")
    email: EmailStr = Field(..., description="Email address")
    phone: str = Field(..., max_length=20, description="Phone number")
    mobile: Optional[str] = Field(None, max_length=20, description="Mobile number")
    address_line1: str = Field(..., max_length=200, description="Address line 1")
    address_line2: Optional[str] = Field(None, max_length=200, description="Address line 2")
    city: str = Field(..., max_length=100, description="City")
    state: str = Field(..., max_length=100, description="State")
    postal_code: str = Field(..., max_length=20, description="Postal code")
    country: str = Field(..., max_length=100, description="Country")
    tax_number: Optional[str] = Field(None, max_length=50, description="Tax number")
    credit_limit: Optional[float] = Field(None, ge=0, description="Credit limit")
    payment_terms: Optional[str] = Field(None, max_length=50, description="Payment terms")
    notes: Optional[str] = Field(None, description="Additional notes")


class CustomerUpdate(BaseModel):
    """Schema for updating a customer."""
    customer_type: Optional[CustomerType] = Field(None, description="Customer type")
    company_name: Optional[str] = Field(None, max_length=200, description="Company name")
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    email: Optional[EmailStr] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    mobile: Optional[str] = Field(None, max_length=20, description="Mobile number")
    address_line1: Optional[str] = Field(None, max_length=200, description="Address line 1")
    address_line2: Optional[str] = Field(None, max_length=200, description="Address line 2")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=100, description="State")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal code")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    tax_number: Optional[str] = Field(None, max_length=50, description="Tax number")
    credit_limit: Optional[float] = Field(None, ge=0, description="Credit limit")
    payment_terms: Optional[str] = Field(None, max_length=50, description="Payment terms")
    notes: Optional[str] = Field(None, description="Additional notes")


class CustomerResponse(BaseModel):
    """Schema for customer response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    customer_code: str
    customer_type: CustomerType
    company_name: Optional[str]
    first_name: str
    last_name: str
    email: str
    phone: str
    mobile: Optional[str]
    address_line1: str
    address_line2: Optional[str]
    city: str
    state: str
    postal_code: str
    country: str
    tax_number: Optional[str]
    credit_limit: Optional[float]
    payment_terms: Optional[str]
    notes: Optional[str]
    status: CustomerStatus
    blacklist_status: BlacklistStatus
    credit_rating: CreditRating
    total_rentals: int
    total_spent: float
    last_rental_date: Optional[date]
    created_at: datetime
    updated_at: datetime
    is_active: bool


class CustomerStatusUpdate(BaseModel):
    """Schema for updating customer status."""
    status: CustomerStatus = Field(..., description="New customer status")
    notes: Optional[str] = Field(None, description="Status update notes")


class CustomerBlacklistUpdate(BaseModel):
    """Schema for updating customer blacklist status."""
    blacklist_status: BlacklistStatus = Field(..., description="New blacklist status")
    blacklist_reason: Optional[str] = Field(None, description="Blacklist reason")
    notes: Optional[str] = Field(None, description="Additional notes")


class CustomerCreditUpdate(BaseModel):
    """Schema for updating customer credit information."""
    credit_limit: Optional[float] = Field(None, ge=0, description="Credit limit")
    credit_rating: Optional[CreditRating] = Field(None, description="Credit rating")
    payment_terms: Optional[str] = Field(None, max_length=50, description="Payment terms")
    notes: Optional[str] = Field(None, description="Additional notes")


class CustomerSearchRequest(BaseModel):
    """Schema for customer search request."""
    search_term: str = Field(..., min_length=2, description="Search term")
    customer_type: Optional[CustomerType] = Field(None, description="Filter by customer type")
    status: Optional[CustomerStatus] = Field(None, description="Filter by status")
    city: Optional[str] = Field(None, description="Filter by city")
    state: Optional[str] = Field(None, description="Filter by state")
    country: Optional[str] = Field(None, description="Filter by country")
    blacklist_status: Optional[BlacklistStatus] = Field(None, description="Filter by blacklist status")
    credit_rating: Optional[CreditRating] = Field(None, description="Filter by credit rating")


class CustomerStatsResponse(BaseModel):
    """Schema for customer statistics response."""
    total_customers: int
    active_customers: int
    inactive_customers: int
    individual_customers: int
    business_customers: int
    blacklisted_customers: int
    customers_by_credit_rating: dict
    customers_by_state: dict
    top_customers_by_rentals: List[dict]
    top_customers_by_spending: List[dict]
    recent_customers: List[CustomerResponse]


class CustomerAddressCreate(BaseModel):
    """Schema for creating customer address."""
    customer_id: UUID = Field(..., description="Customer ID")
    address_type: str = Field(..., max_length=50, description="Address type")
    address_line1: str = Field(..., max_length=200, description="Address line 1")
    address_line2: Optional[str] = Field(None, max_length=200, description="Address line 2")
    city: str = Field(..., max_length=100, description="City")
    state: str = Field(..., max_length=100, description="State")
    postal_code: str = Field(..., max_length=20, description="Postal code")
    country: str = Field(..., max_length=100, description="Country")
    is_default: bool = Field(False, description="Is default address")


class CustomerAddressResponse(BaseModel):
    """Schema for customer address response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    customer_id: UUID
    address_type: str
    address_line1: str
    address_line2: Optional[str]
    city: str
    state: str
    postal_code: str
    country: str
    is_default: bool
    created_at: datetime
    updated_at: datetime
    is_active: bool


class CustomerContactCreate(BaseModel):
    """Schema for creating customer contact."""
    customer_id: UUID = Field(..., description="Customer ID")
    contact_type: str = Field(..., max_length=50, description="Contact type")
    contact_value: str = Field(..., max_length=200, description="Contact value")
    is_primary: bool = Field(False, description="Is primary contact")
    notes: Optional[str] = Field(None, description="Additional notes")


class CustomerContactResponse(BaseModel):
    """Schema for customer contact response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    customer_id: UUID
    contact_type: str
    contact_value: str
    is_primary: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_active: bool


class CustomerDetailResponse(BaseModel):
    """Schema for detailed customer response with addresses and contacts."""
    customer: CustomerResponse
    addresses: List[CustomerAddressResponse]
    contacts: List[CustomerContactResponse]
    rental_history: List[dict]  # Will be populated from rental data
    transaction_summary: dict