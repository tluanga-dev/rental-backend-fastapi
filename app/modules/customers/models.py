from enum import Enum
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
from datetime import datetime
from sqlalchemy import Column, String, Numeric, DateTime, Boolean, Text, Index
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property
import re

from app.db.base import BaseModel

if TYPE_CHECKING:
    from app.modules.transaction_base.models import TransactionHeader


class CustomerType(str, Enum):
    """Customer type enumeration."""
    INDIVIDUAL = "INDIVIDUAL"
    BUSINESS = "BUSINESS"


class CustomerTier(str, Enum):
    """Customer tier enumeration."""
    BRONZE = "BRONZE"
    SILVER = "SILVER"
    GOLD = "GOLD"
    PLATINUM = "PLATINUM"


class CustomerStatus(str, Enum):
    """Customer status enumeration."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    PENDING = "PENDING"


class BlacklistStatus(str, Enum):
    """Blacklist status enumeration."""
    CLEAR = "CLEAR"
    WARNING = "WARNING"
    BLACKLISTED = "BLACKLISTED"


class CreditRating(str, Enum):
    """Credit rating enumeration."""
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"
    NO_RATING = "NO_RATING"


class Customer(BaseModel):
    """
    Customer model for managing customer information.
    
    Attributes:
        customer_code: Unique customer code
        customer_type: Type of customer (INDIVIDUAL or BUSINESS)
        business_name: Company name (for business customers)
        first_name: First name (for individual customers)
        last_name: Last name (for individual customers)
        email: Email address
        phone_number: Phone number
        address: Street address
        city: City
        state: State/Province
        country: Country
        postal_code: Postal/ZIP code
        tax_number: GST/Tax identification number
        customer_tier: Customer tier level
        credit_limit: Credit limit amount
        blacklist_status: Blacklist status
        lifetime_value: Total purchase value
        last_transaction_date: Last transaction date
        notes: Additional notes
        transactions: Customer transactions
    """
    
    __tablename__ = "customers"
    
    customer_code = Column(String(20), nullable=False, unique=True, index=True, comment="Unique customer code")
    customer_type = Column(String(20), nullable=False, comment="Customer type")
    business_name = Column(String(200), nullable=True, comment="Company name")
    first_name = Column(String(100), nullable=True, comment="First name")
    last_name = Column(String(100), nullable=True, comment="Last name")
    email = Column(String(255), nullable=True, comment="Email address")
    phone = Column(String(20), nullable=True, comment="Phone number")
    mobile = Column(String(20), nullable=True, comment="Mobile number")
    address_line1 = Column(Text, nullable=True, comment="Address line 1")
    address_line2 = Column(Text, nullable=True, comment="Address line 2")
    city = Column(String(100), nullable=True, comment="City")
    state = Column(String(100), nullable=True, comment="State/Province")
    country = Column(String(100), nullable=True, comment="Country")
    postal_code = Column(String(20), nullable=True, comment="Postal/ZIP code")
    tax_number = Column(String(50), nullable=True, comment="GST/Tax ID")
    payment_terms = Column(String(50), nullable=True, comment="Payment terms")
    customer_tier = Column(String(20), nullable=False, default=CustomerTier.BRONZE.value, comment="Customer tier")
    credit_limit = Column(Numeric(10, 2), nullable=False, default=0.00, comment="Credit limit")
    status = Column(String(20), nullable=False, default=CustomerStatus.ACTIVE.value, comment="Customer status")
    blacklist_status = Column(String(20), nullable=False, default=BlacklistStatus.CLEAR.value, comment="Blacklist status")
    credit_rating = Column(String(20), nullable=False, default=CreditRating.GOOD.value, comment="Credit rating")
    total_rentals = Column(Numeric(10, 0), nullable=False, default=0, comment="Total number of rentals")
    total_spent = Column(Numeric(12, 2), nullable=False, default=0.00, comment="Total amount spent")
    lifetime_value = Column(Numeric(12, 2), nullable=False, default=0.00, comment="Total purchase value")
    last_transaction_date = Column(DateTime, nullable=True, comment="Last transaction date")
    last_rental_date = Column(DateTime, nullable=True, comment="Last rental date")
    notes = Column(Text, nullable=True, comment="Additional notes")
    
    # Relationships
    # transactions = relationship("TransactionHeader", back_populates="customer", lazy="select")  # Commented out until TransactionHeader is properly configured
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_customer_code', 'customer_code'),
        Index('idx_customer_type', 'customer_type'),
        Index('idx_customer_business_name', 'business_name'),
        Index('idx_customer_name', 'first_name', 'last_name'),
        Index('idx_customer_email', 'email'),
        Index('idx_customer_phone', 'phone'),
        Index('idx_customer_tier', 'customer_tier'),
        Index('idx_customer_blacklist', 'blacklist_status'),
        Index('idx_customer_city', 'city'),
        Index('idx_customer_state', 'state'),
        Index('idx_customer_country', 'country'),
# Removed is_active index - column is inherited from BaseModel
    )
    
    def __init__(
        self,
        customer_code: str,
        customer_type: CustomerType,
        business_name: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        mobile: Optional[str] = None,
        address_line1: Optional[str] = None,
        address_line2: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None,
        postal_code: Optional[str] = None,
        tax_number: Optional[str] = None,
        payment_terms: Optional[str] = None,
        customer_tier: CustomerTier = CustomerTier.BRONZE,
        credit_limit: Decimal = Decimal("0.00"),
        blacklist_status: BlacklistStatus = BlacklistStatus.CLEAR,
        **kwargs
    ):
        """
        Initialize a Customer.
        
        Args:
            customer_code: Unique customer code
            customer_type: Type of customer
            business_name: Company name (for business customers)
            first_name: First name (for individual customers)
            last_name: Last name (for individual customers)
            email: Email address
            phone: Phone number
            mobile: Mobile number
            address_line1: Address line 1
            address_line2: Address line 2
            city: City
            state: State/Province
            country: Country
            postal_code: Postal/ZIP code
            tax_number: GST/Tax identification number
            payment_terms: Payment terms
            customer_tier: Customer tier level
            credit_limit: Credit limit amount
            blacklist_status: Blacklist status
            **kwargs: Additional BaseModel fields
        """
        super().__init__(**kwargs)
        self.customer_code = customer_code
        self.customer_type = customer_type.value if isinstance(customer_type, CustomerType) else customer_type
        self.business_name = business_name
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone = phone
        self.mobile = mobile
        self.address_line1 = address_line1
        self.address_line2 = address_line2
        self.city = city
        self.state = state
        self.country = country
        self.postal_code = postal_code
        self.tax_number = tax_number
        self.payment_terms = payment_terms
        self.customer_tier = customer_tier.value if isinstance(customer_tier, CustomerTier) else customer_tier
        self.credit_limit = credit_limit
        self.status = CustomerStatus.ACTIVE.value
        self.blacklist_status = blacklist_status.value if isinstance(blacklist_status, BlacklistStatus) else blacklist_status
        self.credit_rating = CreditRating.GOOD.value
        self.total_rentals = 0
        self.total_spent = Decimal("0.00")
        self.lifetime_value = Decimal("0.00")
        self._validate()
    
    def _validate(self):
        """Validate customer business rules."""
        # Code validation
        if not self.customer_code or not self.customer_code.strip():
            raise ValueError("Customer code cannot be empty")
        
        if len(self.customer_code) > 20:
            raise ValueError("Customer code cannot exceed 20 characters")
        
        # Type validation
        if self.customer_type not in [ct.value for ct in CustomerType]:
            raise ValueError(f"Invalid customer type: {self.customer_type}")
        
        # Business customer validation
        if self.customer_type == CustomerType.BUSINESS.value:
            if not self.business_name or not self.business_name.strip():
                raise ValueError("Business name is required for business customers")
            if len(self.business_name) > 200:
                raise ValueError("Business name cannot exceed 200 characters")
        
        # Individual customer validation
        if self.customer_type == CustomerType.INDIVIDUAL.value:
            if not self.first_name or not self.first_name.strip():
                raise ValueError("First name is required for individual customers")
            if not self.last_name or not self.last_name.strip():
                raise ValueError("Last name is required for individual customers")
            if self.first_name and len(self.first_name) > 100:
                raise ValueError("First name cannot exceed 100 characters")
            if self.last_name and len(self.last_name) > 100:
                raise ValueError("Last name cannot exceed 100 characters")
        
        # Email validation
        if self.email:
            if len(self.email) > 255:
                raise ValueError("Email cannot exceed 255 characters")
            
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, self.email):
                raise ValueError("Invalid email format")
        
        # Phone validation
        if self.phone:
            if len(self.phone) > 20:
                raise ValueError("Phone number cannot exceed 20 characters")
        
        if self.mobile:
            if len(self.mobile) > 20:
                raise ValueError("Mobile number cannot exceed 20 characters")
        
        # Address validation
        if self.city and len(self.city) > 100:
            raise ValueError("City cannot exceed 100 characters")
        
        if self.state and len(self.state) > 100:
            raise ValueError("State cannot exceed 100 characters")
        
        if self.country and len(self.country) > 100:
            raise ValueError("Country cannot exceed 100 characters")
        
        if self.postal_code and len(self.postal_code) > 20:
            raise ValueError("Postal code cannot exceed 20 characters")
        
        # Tax ID validation
        if self.tax_number and len(self.tax_number) > 50:
            raise ValueError("Tax number cannot exceed 50 characters")
        
        # Tier validation
        if self.customer_tier not in [tier.value for tier in CustomerTier]:
            raise ValueError(f"Invalid customer tier: {self.customer_tier}")
        
        # Blacklist validation
        if self.blacklist_status not in [status.value for status in BlacklistStatus]:
            raise ValueError(f"Invalid blacklist status: {self.blacklist_status}")
        
        # Credit limit validation
        if self.credit_limit is not None and self.credit_limit < 0:
            raise ValueError("Credit limit cannot be negative")
    
    def update_contact_info(
        self,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        mobile: Optional[str] = None,
        address_line1: Optional[str] = None,
        address_line2: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None,
        postal_code: Optional[str] = None,
        updated_by: Optional[str] = None
    ):
        """Update customer contact information."""
        if email is not None:
            if email:
                if len(email) > 255:
                    raise ValueError("Email cannot exceed 255 characters")
                
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, email):
                    raise ValueError("Invalid email format")
            
            self.email = email.strip() if email else None
        
        if phone is not None:
            if phone and len(phone) > 20:
                raise ValueError("Phone number cannot exceed 20 characters")
            self.phone = phone.strip() if phone else None
        
        if mobile is not None:
            if mobile and len(mobile) > 20:
                raise ValueError("Mobile number cannot exceed 20 characters")
            self.mobile = mobile.strip() if mobile else None
        
        if address_line1 is not None:
            self.address_line1 = address_line1.strip() if address_line1 else None
            
        if address_line2 is not None:
            self.address_line2 = address_line2.strip() if address_line2 else None
        
        if city is not None:
            if city and len(city) > 100:
                raise ValueError("City cannot exceed 100 characters")
            self.city = city.strip() if city else None
        
        if state is not None:
            if state and len(state) > 100:
                raise ValueError("State cannot exceed 100 characters")
            self.state = state.strip() if state else None
        
        if country is not None:
            if country and len(country) > 100:
                raise ValueError("Country cannot exceed 100 characters")
            self.country = country.strip() if country else None
        
        if postal_code is not None:
            if postal_code and len(postal_code) > 20:
                raise ValueError("Postal code cannot exceed 20 characters")
            self.postal_code = postal_code.strip() if postal_code else None
        
        self.updated_by = updated_by
    
    def update_tier(self, new_tier: CustomerTier, updated_by: Optional[str] = None):
        """Update customer tier."""
        if new_tier.value not in [tier.value for tier in CustomerTier]:
            raise ValueError(f"Invalid customer tier: {new_tier}")
        
        self.customer_tier = new_tier.value
        self.updated_by = updated_by
    
    def update_credit_limit(self, new_limit: Decimal, updated_by: Optional[str] = None):
        """Update customer credit limit."""
        if new_limit < 0:
            raise ValueError("Credit limit cannot be negative")
        
        self.credit_limit = new_limit
        self.updated_by = updated_by
    
    def blacklist(self, updated_by: Optional[str] = None):
        """Blacklist customer."""
        self.blacklist_status = BlacklistStatus.BLACKLISTED.value
        self.updated_by = updated_by
    
    def clear_blacklist(self, updated_by: Optional[str] = None):
        """Clear blacklist status."""
        self.blacklist_status = BlacklistStatus.CLEAR.value
        self.updated_by = updated_by
    
    def set_warning(self, updated_by: Optional[str] = None):
        """Set warning status."""
        self.blacklist_status = BlacklistStatus.WARNING.value
        self.updated_by = updated_by
    
    def update_lifetime_value(self, amount: Decimal):
        """Update lifetime value."""
        if amount < 0:
            raise ValueError("Lifetime value cannot be negative")
        
        self.lifetime_value = amount
        self.last_transaction_date = datetime.utcnow()
    
    def is_individual(self) -> bool:
        """Check if customer is individual."""
        return self.customer_type == CustomerType.INDIVIDUAL.value
    
    def is_business(self) -> bool:
        """Check if customer is business."""
        return self.customer_type == CustomerType.BUSINESS.value
    
    def is_blacklisted(self) -> bool:
        """Check if customer is blacklisted."""
        return self.blacklist_status == BlacklistStatus.BLACKLISTED.value
    
    def has_warning(self) -> bool:
        """Check if customer has warning status."""
        return self.blacklist_status == BlacklistStatus.WARNING.value
    
    def can_transact(self) -> bool:
        """Check if customer can make transactions."""
        return self.is_active and not self.is_blacklisted()
    
    def get_full_address(self) -> str:
        """Get full formatted address."""
        parts = []
        if self.address:
            parts.append(self.address)
        if self.city:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.postal_code:
            parts.append(self.postal_code)
        if self.country:
            parts.append(self.country)
        return ", ".join(parts)
    
    @property
    def display_name(self) -> str:
        """Get customer display name."""
        if self.is_business():
            return f"{self.business_name} ({self.customer_code})"
        else:
            return f"{self.first_name} {self.last_name} ({self.customer_code})"
    
    @property
    def name(self) -> str:
        """Get customer name."""
        if self.is_business():
            return self.business_name
        else:
            return f"{self.first_name} {self.last_name}"
    
    @property
    def transaction_count(self) -> int:
        """Get number of transactions."""
        return len(self.transactions) if self.transactions else 0
    
    @property
    def tier_display(self) -> str:
        """Get tier display name."""
        tier_names = {
            CustomerTier.BRONZE.value: "Bronze",
            CustomerTier.SILVER.value: "Silver",
            CustomerTier.GOLD.value: "Gold",
            CustomerTier.PLATINUM.value: "Platinum"
        }
        return tier_names.get(self.customer_tier, self.customer_tier)
    
    @property
    def status_display(self) -> str:
        """Get status display name."""
        status_names = {
            BlacklistStatus.CLEAR.value: "Clear",
            BlacklistStatus.WARNING.value: "Warning",
            BlacklistStatus.BLACKLISTED.value: "Blacklisted"
        }
        return status_names.get(self.blacklist_status, self.blacklist_status)
    
    def __str__(self) -> str:
        """String representation of customer."""
        return self.display_name
    
    def __repr__(self) -> str:
        """Developer representation of customer."""
        return (
            f"Customer(id={self.id}, code='{self.customer_code}', "
            f"type='{self.customer_type}', tier='{self.customer_tier}', "
            f"active={self.is_active})"
        )