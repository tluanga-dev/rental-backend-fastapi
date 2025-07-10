from enum import Enum
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Column, String, Text, ForeignKey, Index
from sqlalchemy.orm import relationship, validates
import re

from app.db.base import BaseModel, UUIDType

if TYPE_CHECKING:
    from app.modules.inventory.models import InventoryUnit, StockLevel


class LocationType(str, Enum):
    """Location type enumeration."""
    STORE = "STORE"
    WAREHOUSE = "WAREHOUSE"
    SERVICE_CENTER = "SERVICE_CENTER"


class Location(BaseModel):
    """
    Location model representing physical locations.
    
    Attributes:
        location_code: Unique code for the location
        location_name: Name of the location
        location_type: Type of location (STORE, WAREHOUSE, SERVICE_CENTER)
        address: Street address
        city: City
        state: State/Province
        country: Country
        postal_code: Postal/ZIP code
        contact_number: Phone number
        email: Email address
        manager_user_id: UUID of the manager user
        inventory_units: Inventory units at this location
        stock_levels: Stock levels at this location
    """
    
    __tablename__ = "locations"
    
    location_code = Column(String(20), nullable=False, unique=True, index=True, comment="Unique location code")
    location_name = Column(String(100), nullable=False, comment="Location name")
    location_type = Column(String(20), nullable=False, comment="Location type")
    address = Column(Text, nullable=False, comment="Street address")
    city = Column(String(100), nullable=False, comment="City")
    state = Column(String(100), nullable=False, comment="State/Province")
    country = Column(String(100), nullable=False, comment="Country")
    postal_code = Column(String(20), nullable=True, comment="Postal/ZIP code")
    contact_number = Column(String(20), nullable=True, comment="Phone number")
    email = Column(String(255), nullable=True, comment="Email address")
    manager_user_id = Column(UUIDType(), nullable=True, comment="Manager user ID")
    
    # Relationships
    # inventory_units = relationship("InventoryUnit", back_populates="location", lazy="select")  # Temporarily disabled
    # stock_levels = relationship("StockLevel", back_populates="location", lazy="select")  # Temporarily disabled
    # transactions = relationship("TransactionHeader", back_populates="location", lazy="select")  # Temporarily disabled
    # rental_returns = relationship("RentalReturn", back_populates="return_location", lazy="select")  # Temporarily disabled
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_location_code', 'location_code'),
        Index('idx_location_name', 'location_name'),
        Index('idx_location_type', 'location_type'),
        Index('idx_location_city', 'city'),
        Index('idx_location_state', 'state'),
        Index('idx_location_country', 'country'),
        Index('idx_location_manager', 'manager_user_id'),
# Removed is_active index - column is inherited from BaseModel
    )
    
    def __init__(
        self,
        location_code: str,
        location_name: str,
        location_type: LocationType,
        address: str,
        city: str,
        state: str,
        country: str,
        postal_code: Optional[str] = None,
        contact_number: Optional[str] = None,
        email: Optional[str] = None,
        manager_user_id: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize a Location.
        
        Args:
            location_code: Unique code for the location
            location_name: Name of the location
            location_type: Type of location
            address: Street address
            city: City
            state: State/Province
            country: Country
            postal_code: Postal/ZIP code
            contact_number: Phone number
            email: Email address
            manager_user_id: Manager user ID
            **kwargs: Additional BaseModel fields
        """
        super().__init__(**kwargs)
        self.location_code = location_code
        self.location_name = location_name
        self.location_type = location_type.value if isinstance(location_type, LocationType) else location_type
        self.address = address
        self.city = city
        self.state = state
        self.country = country
        self.postal_code = postal_code
        self.contact_number = contact_number
        self.email = email
        self.manager_user_id = manager_user_id
        self._validate()
    
    def _validate(self):
        """Validate location business rules."""
        # Code validation
        if not self.location_code or not self.location_code.strip():
            raise ValueError("Location code cannot be empty")
        
        if len(self.location_code) > 20:
            raise ValueError("Location code cannot exceed 20 characters")
        
        # Name validation
        if not self.location_name or not self.location_name.strip():
            raise ValueError("Location name cannot be empty")
        
        if len(self.location_name) > 100:
            raise ValueError("Location name cannot exceed 100 characters")
        
        # Type validation
        if self.location_type not in [lt.value for lt in LocationType]:
            raise ValueError(f"Invalid location type: {self.location_type}")
        
        # Address validation
        if not self.address or not self.address.strip():
            raise ValueError("Address cannot be empty")
        
        # City validation
        if not self.city or not self.city.strip():
            raise ValueError("City cannot be empty")
        
        if len(self.city) > 100:
            raise ValueError("City cannot exceed 100 characters")
        
        # State validation
        if not self.state or not self.state.strip():
            raise ValueError("State cannot be empty")
        
        if len(self.state) > 100:
            raise ValueError("State cannot exceed 100 characters")
        
        # Country validation
        if not self.country or not self.country.strip():
            raise ValueError("Country cannot be empty")
        
        if len(self.country) > 100:
            raise ValueError("Country cannot exceed 100 characters")
        
        # Postal code validation
        if self.postal_code and len(self.postal_code) > 20:
            raise ValueError("Postal code cannot exceed 20 characters")
        
        # Email validation
        if self.email:
            if len(self.email) > 255:
                raise ValueError("Email cannot exceed 255 characters")
            
            # Basic email format validation
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, self.email):
                raise ValueError("Invalid email format")
        
        # Contact number validation
        if self.contact_number:
            if len(self.contact_number) > 20:
                raise ValueError("Contact number cannot exceed 20 characters")
            
            # Basic phone number validation (digits, spaces, hyphens, parentheses, plus)
            phone_pattern = r'^[\+]?[0-9\s\-\(\)\.]+$'
            if not re.match(phone_pattern, self.contact_number):
                raise ValueError("Invalid contact number format")
    
    @validates('location_code')
    def validate_location_code(self, key, value):
        """Validate location code."""
        if not value or not value.strip():
            raise ValueError("Location code cannot be empty")
        if len(value) > 20:
            raise ValueError("Location code cannot exceed 20 characters")
        return value.strip().upper()
    
    @validates('location_name')
    def validate_location_name(self, key, value):
        """Validate location name."""
        if not value or not value.strip():
            raise ValueError("Location name cannot be empty")
        if len(value) > 100:
            raise ValueError("Location name cannot exceed 100 characters")
        return value.strip()
    
    @validates('location_type')
    def validate_location_type(self, key, value):
        """Validate location type."""
        if isinstance(value, LocationType):
            return value.value
        if value not in [lt.value for lt in LocationType]:
            raise ValueError(f"Invalid location type: {value}")
        return value
    
    @validates('email')
    def validate_email(self, key, value):
        """Validate email format."""
        if value:
            if len(value) > 255:
                raise ValueError("Email cannot exceed 255 characters")
            
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, value):
                raise ValueError("Invalid email format")
        return value
    
    @validates('contact_number')
    def validate_contact_number(self, key, value):
        """Validate contact number format."""
        if value:
            if len(value) > 20:
                raise ValueError("Contact number cannot exceed 20 characters")
            
            phone_pattern = r'^[\+]?[0-9\s\-\(\)\.]+$'
            if not re.match(phone_pattern, value):
                raise ValueError("Invalid contact number format")
        return value
    
    def update_details(
        self,
        location_name: Optional[str] = None,
        address: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None,
        postal_code: Optional[str] = None,
        updated_by: Optional[str] = None
    ):
        """
        Update location details.
        
        Args:
            location_name: New location name
            address: New address
            city: New city
            state: New state
            country: New country
            postal_code: New postal code
            updated_by: User making the update
        """
        if location_name is not None:
            if not location_name or not location_name.strip():
                raise ValueError("Location name cannot be empty")
            if len(location_name) > 100:
                raise ValueError("Location name cannot exceed 100 characters")
            self.location_name = location_name.strip()
        
        if address is not None:
            if not address or not address.strip():
                raise ValueError("Address cannot be empty")
            self.address = address.strip()
        
        if city is not None:
            if not city or not city.strip():
                raise ValueError("City cannot be empty")
            if len(city) > 100:
                raise ValueError("City cannot exceed 100 characters")
            self.city = city.strip()
        
        if state is not None:
            if not state or not state.strip():
                raise ValueError("State cannot be empty")
            if len(state) > 100:
                raise ValueError("State cannot exceed 100 characters")
            self.state = state.strip()
        
        if country is not None:
            if not country or not country.strip():
                raise ValueError("Country cannot be empty")
            if len(country) > 100:
                raise ValueError("Country cannot exceed 100 characters")
            self.country = country.strip()
        
        if postal_code is not None:
            if postal_code and len(postal_code) > 20:
                raise ValueError("Postal code cannot exceed 20 characters")
            self.postal_code = postal_code.strip() if postal_code else None
        
        self.updated_by = updated_by
    
    def update_contact_info(
        self,
        contact_number: Optional[str] = None,
        email: Optional[str] = None,
        updated_by: Optional[str] = None
    ):
        """
        Update location contact information.
        
        Args:
            contact_number: New contact number
            email: New email address
            updated_by: User making the update
        """
        if contact_number is not None:
            if contact_number:
                if len(contact_number) > 20:
                    raise ValueError("Contact number cannot exceed 20 characters")
                
                phone_pattern = r'^[\+]?[0-9\s\-\(\)\.]+$'
                if not re.match(phone_pattern, contact_number):
                    raise ValueError("Invalid contact number format")
            
            self.contact_number = contact_number.strip() if contact_number else None
        
        if email is not None:
            if email:
                if len(email) > 255:
                    raise ValueError("Email cannot exceed 255 characters")
                
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, email):
                    raise ValueError("Invalid email format")
            
            self.email = email.strip() if email else None
        
        self.updated_by = updated_by
    
    def assign_manager(self, manager_user_id: str, updated_by: Optional[str] = None):
        """
        Assign a manager to the location.
        
        Args:
            manager_user_id: Manager user ID
            updated_by: User making the update
        """
        self.manager_user_id = manager_user_id
        self.updated_by = updated_by
    
    def remove_manager(self, updated_by: Optional[str] = None):
        """
        Remove the manager from the location.
        
        Args:
            updated_by: User making the update
        """
        self.manager_user_id = None
        self.updated_by = updated_by
    
    def get_full_address(self) -> str:
        """Get the full formatted address."""
        parts = [self.address, self.city, self.state]
        if self.postal_code:
            parts.append(self.postal_code)
        parts.append(self.country)
        return ", ".join(parts)
    
    def is_store(self) -> bool:
        """Check if location is a store."""
        return self.location_type == LocationType.STORE.value
    
    def is_warehouse(self) -> bool:
        """Check if location is a warehouse."""
        return self.location_type == LocationType.WAREHOUSE.value
    
    def is_service_center(self) -> bool:
        """Check if location is a service center."""
        return self.location_type == LocationType.SERVICE_CENTER.value
    
    def has_inventory(self) -> bool:
        """Check if location has inventory units."""
        # Temporarily disabled relationship - return False
        return False
    
    def has_stock(self) -> bool:
        """Check if location has stock levels."""
        # Temporarily disabled relationship - return False
        return False
    
    def can_delete(self) -> bool:
        """Check if location can be deleted."""
        # Can only delete if no inventory units or stock levels
        return (
            self.is_active and 
            not self.has_inventory() and 
            not self.has_stock()
        )
    
    def get_location_type_display(self) -> str:
        """Get display name for location type."""
        type_display = {
            LocationType.STORE.value: "Store",
            LocationType.WAREHOUSE.value: "Warehouse",
            LocationType.SERVICE_CENTER.value: "Service Center"
        }
        return type_display.get(self.location_type, self.location_type)
    
    @property
    def display_name(self) -> str:
        """Get display name for the location."""
        return f"{self.location_name} ({self.location_code})"
    
    @property
    def short_address(self) -> str:
        """Get short address (city, state, country)."""
        return f"{self.city}, {self.state}, {self.country}"
    
    @property
    def inventory_count(self) -> int:
        """Get number of inventory units at this location."""
        # Temporarily disabled relationship - return 0
        return 0
    
    @property
    def stock_item_count(self) -> int:
        """Get number of stock items at this location."""
        # Temporarily disabled relationship - return 0
        return 0
    
    def __str__(self) -> str:
        """String representation of location."""
        return self.display_name
    
    def __repr__(self) -> str:
        """Developer representation of location."""
        return (
            f"Location(id={self.id}, code='{self.location_code}', "
            f"name='{self.location_name}', type='{self.location_type}', "
            f"city='{self.city}', active={self.is_active})"
        )