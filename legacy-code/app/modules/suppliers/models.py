from enum import Enum
from typing import Optional
from sqlalchemy import Column, String, Text, Boolean, DateTime, Numeric, Integer, Index
from decimal import Decimal
from datetime import datetime

from app.db.base import BaseModel


class SupplierType(str, Enum):
    """Supplier type enumeration."""
    MANUFACTURER = "MANUFACTURER"
    DISTRIBUTOR = "DISTRIBUTOR"
    WHOLESALER = "WHOLESALER"
    RETAILER = "RETAILER"
    INVENTORY = "INVENTORY"
    SERVICE = "SERVICE"
    DIRECT = "DIRECT"


class SupplierTier(str, Enum):
    """Supplier tier enumeration."""
    PREMIUM = "PREMIUM"
    STANDARD = "STANDARD"
    BASIC = "BASIC"
    TRIAL = "TRIAL"


class SupplierStatus(str, Enum):
    """Supplier status enumeration."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    SUSPENDED = "SUSPENDED"
    BLACKLISTED = "BLACKLISTED"


class PaymentTerms(str, Enum):
    """Payment terms enumeration."""
    IMMEDIATE = "IMMEDIATE"
    NET15 = "NET15"
    NET30 = "NET30"
    NET45 = "NET45"
    NET60 = "NET60"
    NET90 = "NET90"
    COD = "COD"


class Supplier(BaseModel):
    """
    Supplier model for managing supplier information.
    
    Attributes:
        supplier_code: Unique supplier code
        company_name: Supplier company name
        supplier_type: Type of supplier (MANUFACTURER, DISTRIBUTOR, etc.)
        contact_person: Primary contact person
        email: Supplier email address
        phone: Supplier phone number
        mobile: Supplier mobile number
        address_line1: Primary address line
        address_line2: Secondary address line
        city: City
        state: State/Province
        postal_code: Postal/ZIP code
        country: Country
        tax_id: Tax identification number
        payment_terms: Payment terms (NET30, NET45, etc.)
        credit_limit: Credit limit amount
        supplier_tier: Supplier tier (PREMIUM, STANDARD, etc.)
        status: Supplier status (ACTIVE, INACTIVE, etc.)
        quality_rating: Quality rating (0-5)
        delivery_rating: Delivery rating (0-5)
        average_delivery_days: Average delivery time in days
        total_orders: Total number of orders
        total_spend: Total amount spent
        last_order_date: Date of last order
        contract_start_date: Contract start date
        contract_end_date: Contract end date
        notes: Additional notes
        website: Supplier website
        account_manager: Account manager name
        preferred_payment_method: Preferred payment method
        insurance_expiry: Insurance expiry date
        certifications: Certifications held
    """
    
    __tablename__ = "suppliers"
    
    # Core supplier information
    supplier_code = Column(String(50), unique=True, nullable=False, index=True, comment="Unique supplier code")
    company_name = Column(String(255), nullable=False, index=True, comment="Supplier company name")
    supplier_type = Column(String(50), nullable=False, comment="Type of supplier")
    
    # Contact information
    contact_person = Column(String(255), nullable=True, comment="Primary contact person")
    email = Column(String(255), nullable=True, index=True, comment="Supplier email address")
    phone = Column(String(50), nullable=True, comment="Supplier phone number")
    mobile = Column(String(50), nullable=True, comment="Supplier mobile number")
    
    # Address information
    address_line1 = Column(String(255), nullable=True, comment="Primary address line")
    address_line2 = Column(String(255), nullable=True, comment="Secondary address line")
    city = Column(String(100), nullable=True, comment="City")
    state = Column(String(100), nullable=True, comment="State/Province")
    postal_code = Column(String(20), nullable=True, comment="Postal/ZIP code")
    country = Column(String(100), nullable=True, comment="Country")
    
    # Business information
    tax_id = Column(String(50), nullable=True, comment="Tax identification number")
    payment_terms = Column(String(20), nullable=False, default=PaymentTerms.NET30.value, comment="Payment terms")
    credit_limit = Column(Numeric(12, 2), nullable=False, default=0, comment="Credit limit amount")
    supplier_tier = Column(String(20), nullable=False, default=SupplierTier.STANDARD.value, comment="Supplier tier")
    status = Column(String(20), nullable=False, default=SupplierStatus.ACTIVE.value, comment="Supplier status")
    
    # Performance metrics
    quality_rating = Column(Numeric(3, 2), nullable=False, default=0, comment="Quality rating (0-5)")
    delivery_rating = Column(Numeric(3, 2), nullable=False, default=0, comment="Delivery rating (0-5)")
    average_delivery_days = Column(Integer, nullable=False, default=0, comment="Average delivery time in days")
    total_orders = Column(Integer, nullable=False, default=0, comment="Total number of orders")
    total_spend = Column(Numeric(15, 2), nullable=False, default=0, comment="Total amount spent")
    last_order_date = Column(DateTime, nullable=True, comment="Date of last order")
    
    # Contract information
    contract_start_date = Column(DateTime, nullable=True, comment="Contract start date")
    contract_end_date = Column(DateTime, nullable=True, comment="Contract end date")
    
    # Additional information
    notes = Column(Text, nullable=True, comment="Additional notes")
    website = Column(String(255), nullable=True, comment="Supplier website")
    account_manager = Column(String(255), nullable=True, comment="Account manager name")
    preferred_payment_method = Column(String(50), nullable=True, comment="Preferred payment method")
    insurance_expiry = Column(DateTime, nullable=True, comment="Insurance expiry date")
    certifications = Column(Text, nullable=True, comment="Certifications held")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_supplier_code', 'supplier_code'),
        Index('idx_supplier_company_name', 'company_name'),
        Index('idx_supplier_type', 'supplier_type'),
        Index('idx_supplier_status', 'status'),
        Index('idx_supplier_tier', 'supplier_tier'),
        Index('idx_supplier_email', 'email'),
        Index('idx_supplier_payment_terms', 'payment_terms'),
        Index('idx_supplier_last_order', 'last_order_date'),
        Index('idx_supplier_contract_dates', 'contract_start_date', 'contract_end_date'),
        Index('idx_supplier_ratings', 'quality_rating', 'delivery_rating'),
    )
    
    def __init__(
        self,
        supplier_code: str,
        company_name: str,
        supplier_type: SupplierType,
        contact_person: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        mobile: Optional[str] = None,
        address_line1: Optional[str] = None,
        address_line2: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        postal_code: Optional[str] = None,
        country: Optional[str] = None,
        tax_id: Optional[str] = None,
        payment_terms: PaymentTerms = PaymentTerms.NET30,
        credit_limit: Decimal = Decimal("0.00"),
        supplier_tier: SupplierTier = SupplierTier.STANDARD,
        status: SupplierStatus = SupplierStatus.ACTIVE,
        notes: Optional[str] = None,
        website: Optional[str] = None,
        account_manager: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize a Supplier.
        
        Args:
            supplier_code: Unique supplier code
            company_name: Supplier company name
            supplier_type: Type of supplier
            contact_person: Primary contact person
            email: Supplier email address
            phone: Supplier phone number
            mobile: Supplier mobile number
            address_line1: Primary address line
            address_line2: Secondary address line
            city: City
            state: State/Province
            postal_code: Postal/ZIP code
            country: Country
            tax_id: Tax identification number
            payment_terms: Payment terms
            credit_limit: Credit limit amount
            supplier_tier: Supplier tier
            status: Supplier status
            notes: Additional notes
            website: Supplier website
            account_manager: Account manager name
            **kwargs: Additional BaseModel fields
        """
        super().__init__(**kwargs)
        self.supplier_code = supplier_code
        self.company_name = company_name
        self.supplier_type = supplier_type.value if isinstance(supplier_type, SupplierType) else supplier_type
        self.contact_person = contact_person
        self.email = email
        self.phone = phone
        self.mobile = mobile
        self.address_line1 = address_line1
        self.address_line2 = address_line2
        self.city = city
        self.state = state
        self.postal_code = postal_code
        self.country = country
        self.tax_id = tax_id
        self.payment_terms = payment_terms.value if isinstance(payment_terms, PaymentTerms) else payment_terms
        self.credit_limit = float(credit_limit)
        self.supplier_tier = supplier_tier.value if isinstance(supplier_tier, SupplierTier) else supplier_tier
        self.status = status.value if isinstance(status, SupplierStatus) else status
        self.notes = notes
        self.website = website
        self.account_manager = account_manager
        self.quality_rating = 0.0
        self.delivery_rating = 0.0
        self.average_delivery_days = 0
        self.total_orders = 0
        self.total_spend = 0.0
        self._validate()
    
    def _validate(self):
        """Validate supplier business rules."""
        if not self.supplier_code or not self.supplier_code.strip():
            raise ValueError("Supplier code cannot be empty")
        
        if len(self.supplier_code) > 50:
            raise ValueError("Supplier code cannot exceed 50 characters")
        
        if not self.company_name or not self.company_name.strip():
            raise ValueError("Company name cannot be empty")
        
        if len(self.company_name) > 255:
            raise ValueError("Company name cannot exceed 255 characters")
        
        if self.supplier_type not in [t.value for t in SupplierType]:
            raise ValueError(f"Invalid supplier type: {self.supplier_type}")
        
        if self.email and len(self.email) > 255:
            raise ValueError("Email cannot exceed 255 characters")
        
        if self.email and "@" not in self.email:
            raise ValueError("Invalid email format")
        
        if self.phone and len(self.phone) > 50:
            raise ValueError("Phone number cannot exceed 50 characters")
        
        if self.mobile and len(self.mobile) > 50:
            raise ValueError("Mobile number cannot exceed 50 characters")
        
        if self.credit_limit < 0:
            raise ValueError("Credit limit cannot be negative")
        
        if self.status not in [s.value for s in SupplierStatus]:
            raise ValueError(f"Invalid supplier status: {self.status}")
        
        if self.supplier_tier not in [t.value for t in SupplierTier]:
            raise ValueError(f"Invalid supplier tier: {self.supplier_tier}")
        
        if self.payment_terms not in [p.value for p in PaymentTerms]:
            raise ValueError(f"Invalid payment terms: {self.payment_terms}")
    
    def update_performance_metrics(
        self,
        quality_rating: Optional[float] = None,
        delivery_rating: Optional[float] = None,
        average_delivery_days: Optional[int] = None,
        total_orders: Optional[int] = None,
        total_spend: Optional[float] = None,
        last_order_date: Optional[datetime] = None
    ):
        """Update supplier performance metrics."""
        if quality_rating is not None:
            if not 0 <= quality_rating <= 5:
                raise ValueError("Quality rating must be between 0 and 5")
            self.quality_rating = quality_rating
        
        if delivery_rating is not None:
            if not 0 <= delivery_rating <= 5:
                raise ValueError("Delivery rating must be between 0 and 5")
            self.delivery_rating = delivery_rating
        
        if average_delivery_days is not None:
            if average_delivery_days < 0:
                raise ValueError("Average delivery days cannot be negative")
            self.average_delivery_days = average_delivery_days
        
        if total_orders is not None:
            if total_orders < 0:
                raise ValueError("Total orders cannot be negative")
            self.total_orders = total_orders
        
        if total_spend is not None:
            if total_spend < 0:
                raise ValueError("Total spend cannot be negative")
            self.total_spend = total_spend
        
        if last_order_date is not None:
            self.last_order_date = last_order_date
    
    def activate(self, updated_by: Optional[str] = None):
        """Activate supplier."""
        self.status = SupplierStatus.ACTIVE.value
        self.updated_by = updated_by
    
    def deactivate(self, updated_by: Optional[str] = None):
        """Deactivate supplier."""
        self.status = SupplierStatus.INACTIVE.value
        self.updated_by = updated_by
    
    def suspend(self, updated_by: Optional[str] = None):
        """Suspend supplier."""
        self.status = SupplierStatus.SUSPENDED.value
        self.updated_by = updated_by
    
    def blacklist(self, updated_by: Optional[str] = None):
        """Blacklist supplier."""
        self.status = SupplierStatus.BLACKLISTED.value
        self.updated_by = updated_by
    
    def approve(self, updated_by: Optional[str] = None):
        """Approve supplier."""
        self.status = SupplierStatus.APPROVED.value
        self.updated_by = updated_by
    
    def is_active_supplier(self) -> bool:
        """Check if supplier is active."""
        return self.status == SupplierStatus.ACTIVE.value and self.is_active
    
    def is_approved(self) -> bool:
        """Check if supplier is approved."""
        return self.status == SupplierStatus.APPROVED.value
    
    def is_suspended(self) -> bool:
        """Check if supplier is suspended."""
        return self.status == SupplierStatus.SUSPENDED.value
    
    def is_blacklisted(self) -> bool:
        """Check if supplier is blacklisted."""
        return self.status == SupplierStatus.BLACKLISTED.value
    
    def can_place_order(self) -> bool:
        """Check if supplier can receive orders."""
        return self.is_active_supplier() and self.status in [
            SupplierStatus.ACTIVE.value,
            SupplierStatus.APPROVED.value
        ]
    
    @property
    def full_address(self) -> str:
        """Get formatted full address."""
        parts = [self.address_line1, self.address_line2, self.city, self.state, self.postal_code, self.country]
        return ", ".join(part for part in parts if part)
    
    @property
    def display_name(self) -> str:
        """Get supplier display name."""
        return f"{self.company_name} ({self.supplier_code})"
    
    @property
    def overall_rating(self) -> float:
        """Get overall supplier rating (average of quality and delivery)."""
        if self.quality_rating > 0 and self.delivery_rating > 0:
            return (self.quality_rating + self.delivery_rating) / 2
        return 0.0
    
    def __str__(self) -> str:
        """String representation of supplier."""
        return self.display_name
    
    def __repr__(self) -> str:
        """Developer representation of supplier."""
        return (
            f"Supplier(id={self.id}, code='{self.supplier_code}', "
            f"company='{self.company_name}', type='{self.supplier_type}', "
            f"status='{self.status}', active={self.is_active})"
        )