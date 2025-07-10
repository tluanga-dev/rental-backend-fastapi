from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, validator
from decimal import Decimal
from uuid import UUID

from .models import SupplierType, SupplierTier, SupplierStatus, PaymentTerms


class SupplierCreate(BaseModel):
    """Schema for creating a new supplier."""
    supplier_code: str = Field(..., max_length=50, description="Unique supplier code")
    company_name: str = Field(..., max_length=255, description="Supplier company name")
    supplier_type: SupplierType = Field(..., description="Type of supplier")
    contact_person: Optional[str] = Field(None, max_length=255, description="Primary contact person")
    email: Optional[str] = Field(None, max_length=255, description="Supplier email address")
    phone: Optional[str] = Field(None, max_length=50, description="Supplier phone number")
    mobile: Optional[str] = Field(None, max_length=50, description="Supplier mobile number")
    address_line1: Optional[str] = Field(None, max_length=255, description="Primary address line")
    address_line2: Optional[str] = Field(None, max_length=255, description="Secondary address line")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=100, description="State/Province")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal/ZIP code")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    tax_id: Optional[str] = Field(None, max_length=50, description="Tax identification number")
    payment_terms: PaymentTerms = Field(PaymentTerms.NET30, description="Payment terms")
    credit_limit: Decimal = Field(Decimal("0.00"), ge=0, description="Credit limit amount")
    supplier_tier: SupplierTier = Field(SupplierTier.STANDARD, description="Supplier tier")
    status: SupplierStatus = Field(SupplierStatus.ACTIVE, description="Supplier status")
    notes: Optional[str] = Field(None, description="Additional notes")
    website: Optional[str] = Field(None, max_length=255, description="Supplier website")
    account_manager: Optional[str] = Field(None, max_length=255, description="Account manager name")
    preferred_payment_method: Optional[str] = Field(None, max_length=50, description="Preferred payment method")
    insurance_expiry: Optional[datetime] = Field(None, description="Insurance expiry date")
    certifications: Optional[str] = Field(None, description="Certifications held")
    contract_start_date: Optional[datetime] = Field(None, description="Contract start date")
    contract_end_date: Optional[datetime] = Field(None, description="Contract end date")

    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v

    @validator('website')
    def validate_website(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
            return f'https://{v}'
        return v


class SupplierUpdate(BaseModel):
    """Schema for updating a supplier."""
    company_name: Optional[str] = Field(None, max_length=255, description="Supplier company name")
    supplier_type: Optional[SupplierType] = Field(None, description="Type of supplier")
    contact_person: Optional[str] = Field(None, max_length=255, description="Primary contact person")
    email: Optional[str] = Field(None, max_length=255, description="Supplier email address")
    phone: Optional[str] = Field(None, max_length=50, description="Supplier phone number")
    mobile: Optional[str] = Field(None, max_length=50, description="Supplier mobile number")
    address_line1: Optional[str] = Field(None, max_length=255, description="Primary address line")
    address_line2: Optional[str] = Field(None, max_length=255, description="Secondary address line")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=100, description="State/Province")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal/ZIP code")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    tax_id: Optional[str] = Field(None, max_length=50, description="Tax identification number")
    payment_terms: Optional[PaymentTerms] = Field(None, description="Payment terms")
    credit_limit: Optional[Decimal] = Field(None, ge=0, description="Credit limit amount")
    supplier_tier: Optional[SupplierTier] = Field(None, description="Supplier tier")
    status: Optional[SupplierStatus] = Field(None, description="Supplier status")
    notes: Optional[str] = Field(None, description="Additional notes")
    website: Optional[str] = Field(None, max_length=255, description="Supplier website")
    account_manager: Optional[str] = Field(None, max_length=255, description="Account manager name")
    preferred_payment_method: Optional[str] = Field(None, max_length=50, description="Preferred payment method")
    insurance_expiry: Optional[datetime] = Field(None, description="Insurance expiry date")
    certifications: Optional[str] = Field(None, description="Certifications held")
    contract_start_date: Optional[datetime] = Field(None, description="Contract start date")
    contract_end_date: Optional[datetime] = Field(None, description="Contract end date")

    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v

    @validator('website')
    def validate_website(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
            return f'https://{v}'
        return v


class SupplierStatusUpdate(BaseModel):
    """Schema for updating supplier status."""
    status: SupplierStatus = Field(..., description="New supplier status")
    notes: Optional[str] = Field(None, description="Status change notes")


class SupplierResponse(BaseModel):
    """Schema for supplier response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    supplier_code: str
    company_name: str
    supplier_type: str
    contact_person: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    mobile: Optional[str]
    address_line1: Optional[str]
    address_line2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    postal_code: Optional[str]
    country: Optional[str]
    tax_id: Optional[str]
    payment_terms: str
    credit_limit: Decimal
    supplier_tier: str
    status: str
    quality_rating: Decimal
    delivery_rating: Decimal
    average_delivery_days: int
    total_orders: int
    total_spend: Decimal
    last_order_date: Optional[datetime]
    notes: Optional[str]
    website: Optional[str]
    account_manager: Optional[str]
    preferred_payment_method: Optional[str]
    insurance_expiry: Optional[datetime]
    certifications: Optional[str]
    contract_start_date: Optional[datetime]
    contract_end_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    is_active: bool


class SupplierDetailResponse(SupplierResponse):
    """Schema for detailed supplier response with additional information."""
    full_address: str
    display_name: str
    overall_rating: float
    can_place_order: bool
    is_approved: bool
    is_suspended: bool
    is_blacklisted: bool


class SupplierListResponse(BaseModel):
    """Schema for supplier list response."""
    suppliers: list[SupplierResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class SupplierStatsResponse(BaseModel):
    """Schema for supplier statistics response."""
    total_suppliers: int
    active_suppliers: int
    inactive_suppliers: int
    inventory_suppliers: int
    service_suppliers: int
    approved_suppliers: int
    pending_suppliers: int
    suspended_suppliers: int
    blacklisted_suppliers: int
    average_quality_rating: float
    average_delivery_rating: float
    suppliers_by_type: dict[str, int]
    suppliers_by_tier: dict[str, int]
    suppliers_by_status: dict[str, int]
    suppliers_by_country: dict[str, int]
    top_suppliers_by_orders: list[dict]
    top_suppliers_by_spend: list[dict]
    contract_expiring_soon: list[dict]
    recent_suppliers: list[SupplierResponse]


class SupplierSearchRequest(BaseModel):
    """Schema for supplier search request."""
    search_term: str = Field(..., min_length=2, max_length=100, description="Search term")
    supplier_type: Optional[SupplierType] = Field(None, description="Filter by supplier type")
    status: Optional[SupplierStatus] = Field(None, description="Filter by status")
    supplier_tier: Optional[SupplierTier] = Field(None, description="Filter by supplier tier")
    payment_terms: Optional[PaymentTerms] = Field(None, description="Filter by payment terms")
    country: Optional[str] = Field(None, max_length=100, description="Filter by country")
    min_quality_rating: Optional[float] = Field(None, ge=0, le=5, description="Minimum quality rating")
    max_quality_rating: Optional[float] = Field(None, ge=0, le=5, description="Maximum quality rating")
    min_delivery_rating: Optional[float] = Field(None, ge=0, le=5, description="Minimum delivery rating")
    max_delivery_rating: Optional[float] = Field(None, ge=0, le=5, description="Maximum delivery rating")
    contract_expiring_days: Optional[int] = Field(None, ge=0, le=365, description="Contract expiring within days")
    active_only: bool = Field(True, description="Show only active suppliers")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Page size")
    sort_by: str = Field("company_name", description="Sort field")
    sort_order: str = Field("asc", pattern="^(asc|desc)$", description="Sort order")


class SupplierPerformanceUpdate(BaseModel):
    """Schema for updating supplier performance metrics."""
    quality_rating: Optional[float] = Field(None, ge=0, le=5, description="Quality rating (0-5)")
    delivery_rating: Optional[float] = Field(None, ge=0, le=5, description="Delivery rating (0-5)")
    average_delivery_days: Optional[int] = Field(None, ge=0, description="Average delivery time in days")
    total_orders: Optional[int] = Field(None, ge=0, description="Total number of orders")
    total_spend: Optional[Decimal] = Field(None, ge=0, description="Total amount spent")
    last_order_date: Optional[datetime] = Field(None, description="Date of last order")
    notes: Optional[str] = Field(None, description="Performance update notes")


class SupplierContactUpdate(BaseModel):
    """Schema for updating supplier contact information."""
    contact_person: Optional[str] = Field(None, max_length=255, description="Primary contact person")
    email: Optional[str] = Field(None, max_length=255, description="Supplier email address")
    phone: Optional[str] = Field(None, max_length=50, description="Supplier phone number")
    mobile: Optional[str] = Field(None, max_length=50, description="Supplier mobile number")
    website: Optional[str] = Field(None, max_length=255, description="Supplier website")
    account_manager: Optional[str] = Field(None, max_length=255, description="Account manager name")
    preferred_payment_method: Optional[str] = Field(None, max_length=50, description="Preferred payment method")
    notes: Optional[str] = Field(None, description="Contact update notes")

    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v

    @validator('website')
    def validate_website(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
            return f'https://{v}'
        return v


class SupplierAddressUpdate(BaseModel):
    """Schema for updating supplier address information."""
    address_line1: Optional[str] = Field(None, max_length=255, description="Primary address line")
    address_line2: Optional[str] = Field(None, max_length=255, description="Secondary address line")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=100, description="State/Province")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal/ZIP code")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    notes: Optional[str] = Field(None, description="Address update notes")


class SupplierContractUpdate(BaseModel):
    """Schema for updating supplier contract information."""
    contract_start_date: Optional[datetime] = Field(None, description="Contract start date")
    contract_end_date: Optional[datetime] = Field(None, description="Contract end date")
    payment_terms: Optional[PaymentTerms] = Field(None, description="Payment terms")
    credit_limit: Optional[Decimal] = Field(None, ge=0, description="Credit limit amount")
    supplier_tier: Optional[SupplierTier] = Field(None, description="Supplier tier")
    insurance_expiry: Optional[datetime] = Field(None, description="Insurance expiry date")
    certifications: Optional[str] = Field(None, description="Certifications held")
    notes: Optional[str] = Field(None, description="Contract update notes")

    @validator('contract_end_date')
    def validate_contract_dates(cls, v, values):
        if v and 'contract_start_date' in values and values['contract_start_date'] and v <= values['contract_start_date']:
            raise ValueError('Contract end date must be after start date')
        return v