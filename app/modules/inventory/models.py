from enum import Enum
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
from datetime import datetime
from sqlalchemy import Column, String, Numeric, Boolean, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

from app.db.base import BaseModel, UUIDType, Base, TimestampMixin, AuditMixin
from uuid import uuid4

if TYPE_CHECKING:
    from app.modules.master_data.item_master.models import Item
    from app.modules.master_data.locations.models import Location


class ItemStatus(str, Enum):
    """Item status enumeration."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DISCONTINUED = "DISCONTINUED"


class InventoryUnitStatus(str, Enum):
    """Inventory unit status enumeration."""
    AVAILABLE = "AVAILABLE"
    RENTED = "RENTED"
    SOLD = "SOLD"
    MAINTENANCE = "MAINTENANCE"
    DAMAGED = "DAMAGED"
    RETIRED = "RETIRED"


class InventoryUnitCondition(str, Enum):
    """Inventory unit condition enumeration."""
    NEW = "NEW"
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"
    DAMAGED = "DAMAGED"


class MovementType(str, Enum):
    """Stock movement type enumeration."""
    PURCHASE = "PURCHASE"
    SALE = "SALE"
    RENTAL_OUT = "RENTAL_OUT"
    RENTAL_RETURN = "RENTAL_RETURN"
    ADJUSTMENT_POSITIVE = "ADJUSTMENT_POSITIVE"
    ADJUSTMENT_NEGATIVE = "ADJUSTMENT_NEGATIVE"
    DAMAGE_LOSS = "DAMAGE_LOSS"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"
    SYSTEM_CORRECTION = "SYSTEM_CORRECTION"
    INITIAL_STOCK = "INITIAL_STOCK"


class ReferenceType(str, Enum):
    """Stock movement reference type enumeration."""
    TRANSACTION = "TRANSACTION"
    MANUAL_ADJUSTMENT = "MANUAL_ADJUSTMENT"
    SYSTEM_CORRECTION = "SYSTEM_CORRECTION"
    BULK_IMPORT = "BULK_IMPORT"
    MAINTENANCE = "MAINTENANCE"
    INVENTORY_COUNT = "INVENTORY_COUNT"



class InventoryUnit(BaseModel):
    """
    Inventory unit model for tracking individual units of items.
    
    Attributes:
        item_id: Item ID
        location_id: Location ID
        unit_code: Unique unit code
        serial_number: Serial number
        status: Unit status
        condition: Unit condition
        purchase_date: Purchase date
        purchase_price: Purchase price
        warranty_expiry: Warranty expiry date
        last_maintenance_date: Last maintenance date
        next_maintenance_date: Next maintenance date
        notes: Additional notes
        item: Item relationship
        location: Location relationship
    """
    
    __tablename__ = "inventory_units"
    
    item_id = Column(UUIDType(), ForeignKey("items.id"), nullable=False, comment="Item ID")
    location_id = Column(UUIDType(), ForeignKey("locations.id"), nullable=False, comment="Location ID")
    unit_code = Column(String(50), nullable=False, unique=True, index=True, comment="Unique unit code")
    serial_number = Column(String(100), nullable=True, comment="Serial number")
    status = Column(String(20), nullable=False, default=InventoryUnitStatus.AVAILABLE.value, comment="Unit status")
    condition = Column(String(20), nullable=False, default=InventoryUnitCondition.NEW.value, comment="Unit condition")
    purchase_date = Column(DateTime, nullable=True, comment="Purchase date")
    purchase_price = Column(Numeric(10, 2), nullable=False, default=0.00, comment="Purchase price")
    warranty_expiry = Column(DateTime, nullable=True, comment="Warranty expiry date")
    last_maintenance_date = Column(DateTime, nullable=True, comment="Last maintenance date")
    next_maintenance_date = Column(DateTime, nullable=True, comment="Next maintenance date")
    notes = Column(Text, nullable=True, comment="Additional notes")
    
    # Relationships
    item = relationship("Item", back_populates="inventory_units", lazy="select")
    # location = relationship("Location", back_populates="inventory_units", lazy="select")  # Temporarily disabled
    # transaction_lines = relationship("TransactionLine", back_populates="inventory_unit", lazy="select")  # Temporarily disabled
    # return_lines = relationship("RentalReturnLine", back_populates="inventory_unit", lazy="select")  # Disabled - no model exists
    # inspection_reports = relationship("InspectionReport", back_populates="inventory_unit", lazy="select")  # Disabled - no model exists
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_inventory_unit_code', 'unit_code'),
        Index('idx_inventory_unit_item', 'item_id'),
        Index('idx_inventory_unit_location', 'location_id'),
        Index('idx_inventory_unit_status', 'status'),
        Index('idx_inventory_unit_condition', 'condition'),
        Index('idx_inventory_unit_serial', 'serial_number'),
# Removed is_active index - column is inherited from BaseModel
    )
    
    def __init__(
        self,
        item_id: str,
        location_id: str,
        unit_code: str,
        serial_number: Optional[str] = None,
        status: InventoryUnitStatus = InventoryUnitStatus.AVAILABLE,
        condition: InventoryUnitCondition = InventoryUnitCondition.NEW,
        purchase_price: Decimal = Decimal("0.00"),
        **kwargs
    ):
        """
        Initialize an Inventory Unit.
        
        Args:
            item_id: Item ID
            location_id: Location ID
            unit_code: Unique unit code
            serial_number: Serial number
            status: Unit status
            condition: Unit condition
            purchase_price: Purchase price
            **kwargs: Additional BaseModel fields
        """
        super().__init__(**kwargs)
        self.item_id = item_id
        self.location_id = location_id
        self.unit_code = unit_code
        self.serial_number = serial_number
        self.status = status.value if isinstance(status, InventoryUnitStatus) else status
        self.condition = condition.value if isinstance(condition, InventoryUnitCondition) else condition
        self.purchase_price = purchase_price
        self._validate()
    
    def _validate(self):
        """Validate inventory unit business rules."""
        # Code validation
        if not self.unit_code or not self.unit_code.strip():
            raise ValueError("Unit code cannot be empty")
        
        if len(self.unit_code) > 50:
            raise ValueError("Unit code cannot exceed 50 characters")
        
        # Serial number validation
        if self.serial_number and len(self.serial_number) > 100:
            raise ValueError("Serial number cannot exceed 100 characters")
        
        # Status validation
        if self.status not in [status.value for status in InventoryUnitStatus]:
            raise ValueError(f"Invalid unit status: {self.status}")
        
        # Condition validation
        if self.condition not in [condition.value for condition in InventoryUnitCondition]:
            raise ValueError(f"Invalid unit condition: {self.condition}")
        
        # Price validation
        if self.purchase_price < 0:
            raise ValueError("Purchase price cannot be negative")
    
    def is_available(self) -> bool:
        """Check if unit is available."""
        return self.status == InventoryUnitStatus.AVAILABLE.value and self.is_active
    
    def is_rented(self) -> bool:
        """Check if unit is rented."""
        return self.status == InventoryUnitStatus.RENTED.value
    
    def is_sold(self) -> bool:
        """Check if unit is sold."""
        return self.status == InventoryUnitStatus.SOLD.value
    
    def is_in_maintenance(self) -> bool:
        """Check if unit is in maintenance."""
        return self.status == InventoryUnitStatus.MAINTENANCE.value
    
    def is_damaged(self) -> bool:
        """Check if unit is damaged."""
        return self.status == InventoryUnitStatus.DAMAGED.value
    
    def is_retired(self) -> bool:
        """Check if unit is retired."""
        return self.status == InventoryUnitStatus.RETIRED.value
    
    def rent_out(self, updated_by: Optional[str] = None):
        """Mark unit as rented."""
        if not self.is_available():
            raise ValueError("Unit is not available for rental")
        
        self.status = InventoryUnitStatus.RENTED.value
        self.updated_by = updated_by
    
    def return_from_rent(self, condition: Optional[InventoryUnitCondition] = None, updated_by: Optional[str] = None):
        """Return unit from rental."""
        if not self.is_rented():
            raise ValueError("Unit is not currently rented")
        
        self.status = InventoryUnitStatus.AVAILABLE.value
        if condition:
            self.condition = condition.value
        
        self.updated_by = updated_by
    
    def mark_as_sold(self, updated_by: Optional[str] = None):
        """Mark unit as sold."""
        if not self.is_available():
            raise ValueError("Unit is not available for sale")
        
        self.status = InventoryUnitStatus.SOLD.value
        self.updated_by = updated_by
    
    def send_for_maintenance(self, updated_by: Optional[str] = None):
        """Send unit for maintenance."""
        self.status = InventoryUnitStatus.MAINTENANCE.value
        self.last_maintenance_date = datetime.utcnow()
        self.updated_by = updated_by
    
    def return_from_maintenance(self, condition: InventoryUnitCondition, updated_by: Optional[str] = None):
        """Return unit from maintenance."""
        if not self.is_in_maintenance():
            raise ValueError("Unit is not in maintenance")
        
        self.status = InventoryUnitStatus.AVAILABLE.value
        self.condition = condition.value
        self.updated_by = updated_by
    
    def mark_as_damaged(self, updated_by: Optional[str] = None):
        """Mark unit as damaged."""
        self.status = InventoryUnitStatus.DAMAGED.value
        self.condition = InventoryUnitCondition.DAMAGED.value
        self.updated_by = updated_by
    
    def retire(self, updated_by: Optional[str] = None):
        """Retire unit."""
        self.status = InventoryUnitStatus.RETIRED.value
        self.updated_by = updated_by
    
    @property
    def display_name(self) -> str:
        """Get unit display name."""
        return f"{self.unit_code}"
    
    @property
    def full_display_name(self) -> str:
        """Get full unit display name with item info."""
        if self.item:
            return f"{self.item.item_name} - {self.unit_code}"
        return self.unit_code
    
    def __str__(self) -> str:
        """String representation of inventory unit."""
        return self.full_display_name
    
    def __repr__(self) -> str:
        """Developer representation of inventory unit."""
        return (
            f"InventoryUnit(id={self.id}, code='{self.unit_code}', "
            f"status='{self.status}', condition='{self.condition}', "
            f"active={self.is_active})"
        )


class StockLevel(BaseModel):
    """
    Stock level model for tracking item quantities at locations.
    
    This model tracks the current stock levels for items at specific locations,
    including available quantities and quantities currently on rent.
    
    Attributes:
        item_id: Item ID
        location_id: Location ID
        quantity_on_hand: Total quantity currently in stock
        quantity_available: Quantity available for rent/sale
        quantity_on_rent: Quantity currently rented out
        item: Item relationship
        location: Location relationship
        stock_movements: All stock movements for this stock level
    """
    
    __tablename__ = "stock_levels"
    
    item_id = Column(UUIDType(), ForeignKey("items.id"), nullable=False, comment="Item ID")
    location_id = Column(UUIDType(), ForeignKey("locations.id"), nullable=False, comment="Location ID")
    quantity_on_hand = Column(Numeric(10, 2), nullable=False, default=0, comment="Current quantity on hand")
    quantity_available = Column(Numeric(10, 2), nullable=False, default=0, comment="Available quantity")
    quantity_on_rent = Column(Numeric(10, 2), nullable=False, default=0, comment="Quantity currently on rent")
    
    # Relationships
    item = relationship("Item", back_populates="stock_levels", lazy="select")
    # location = relationship("Location", back_populates="stock_levels", lazy="select")  # Temporarily disabled
    stock_movements = relationship("StockMovement", back_populates="stock_level", lazy="select", cascade="all, delete-orphan")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_stock_level_item', 'item_id'),
        Index('idx_stock_level_location', 'location_id'),
        Index('idx_stock_level_item_location', 'item_id', 'location_id', unique=True),
# Removed is_active index - column is inherited from BaseModel
    )
    
    def __init__(
        self,
        item_id: str,
        location_id: str,
        quantity_on_hand: Decimal = Decimal("0"),
        **kwargs
    ):
        """
        Initialize a Stock Level.
        
        Args:
            item_id: Item ID
            location_id: Location ID
            quantity_on_hand: Current quantity on hand
            **kwargs: Additional BaseModel fields
        """
        super().__init__(**kwargs)
        self.item_id = item_id
        self.location_id = location_id
        self.quantity_on_hand = quantity_on_hand
        self.quantity_available = quantity_on_hand
        self.quantity_on_rent = Decimal("0")
        self._validate()
    
    def _validate(self):
        """Validate stock level business rules."""
        # Validate non-negative quantities
        if self.quantity_on_hand < 0:
            raise ValueError("Quantity on hand cannot be negative")
        
        if self.quantity_available < 0:
            raise ValueError("Available quantity cannot be negative")
        
        if self.quantity_on_rent < 0:
            raise ValueError("Quantity on rent cannot be negative")
        
        # Validate quantity logic
        total_allocated = self.quantity_available + self.quantity_on_rent
        if total_allocated > self.quantity_on_hand:
            raise ValueError("Total allocated quantities cannot exceed quantity on hand")
    
    def adjust_quantity(self, adjustment: Decimal, updated_by: Optional[str] = None):
        """Adjust quantity on hand."""
        new_quantity = self.quantity_on_hand + adjustment
        
        if new_quantity < 0:
            raise ValueError("Quantity adjustment would result in negative stock")
        
        # Maintain proportional allocation if reducing stock
        if adjustment < 0 and self.quantity_on_hand > 0:
            ratio = new_quantity / self.quantity_on_hand
            self.quantity_available = self.quantity_available * ratio
            self.quantity_on_rent = self.quantity_on_rent * ratio
        
        self.quantity_on_hand = new_quantity
        
        # Ensure available quantity doesn't exceed total
        if self.quantity_available > new_quantity:
            self.quantity_available = new_quantity
        
        self.updated_by = updated_by
        self._validate()
    
    def rent_out_quantity(self, quantity: Decimal, updated_by: Optional[str] = None):
        """Move quantity from available to on rent."""
        if quantity < 0:
            raise ValueError("Cannot rent negative quantity")
        
        if quantity > self.quantity_available:
            raise ValueError("Cannot rent more than available quantity")
        
        self.quantity_available -= quantity
        self.quantity_on_rent += quantity
        self.updated_by = updated_by
        self._validate()
    
    def return_from_rent(self, quantity: Decimal, updated_by: Optional[str] = None):
        """Move quantity from on rent back to available."""
        if quantity < 0:
            raise ValueError("Cannot return negative quantity")
        
        if quantity > self.quantity_on_rent:
            raise ValueError("Cannot return more than rented quantity")
        
        self.quantity_on_rent -= quantity
        self.quantity_available += quantity
        self.updated_by = updated_by
        self._validate()
    
    def is_available_for_rent(self, quantity: Decimal = Decimal("1")) -> bool:
        """Check if specified quantity is available for rent."""
        return self.quantity_available >= quantity and self.is_active
    
    def has_rented_quantity(self, quantity: Decimal = Decimal("1")) -> bool:
        """Check if specified quantity is currently on rent."""
        return self.quantity_on_rent >= quantity
    
    @property
    def display_name(self) -> str:
        """Get stock level display name."""
        item_name = "Unknown Item"
        location_name = "Unknown Location"
        
        # Check if relationships are loaded
        if hasattr(self, 'item') and self.item:
            item_name = self.item.item_name
        elif hasattr(self, 'item_id') and self.item_id:
            item_name = f"Item {self.item_id}"
            
        if hasattr(self, 'location') and self.location:
            location_name = self.location.location_name
        elif hasattr(self, 'location_id') and self.location_id:
            location_name = f"Location {self.location_id}"
            
        return f"{item_name} @ {location_name}"
    
    def __str__(self) -> str:
        """String representation of stock level."""
        return self.display_name
    
    def __repr__(self) -> str:
        """Developer representation of stock level."""
        return (
            f"StockLevel(id={self.id}, item_id={self.item_id}, "
            f"location_id={self.location_id}, on_hand={self.quantity_on_hand}, "
            f"available={self.quantity_available}, on_rent={self.quantity_on_rent}, "
            f"active={self.is_active})"
        )


class SKUSequence(BaseModel):
    """
    SKU sequence tracking model for generating unique SKUs.
    
    This model tracks the next sequence number for each brand-category combination
    to ensure unique SKU generation.
    
    Attributes:
        brand_code: Brand code for SKU generation
        category_code: Category code for SKU generation
        next_sequence: Next sequence number to use
    """
    
    __tablename__ = "sku_sequences"
    
    brand_code = Column(String(20), nullable=True, comment="Brand code")
    category_code = Column(String(20), nullable=True, comment="Category code")
    next_sequence = Column(String(10), nullable=False, default="1", comment="Next sequence number")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_sku_sequence_brand_category', 'brand_code', 'category_code', unique=True),
        Index('idx_sku_sequence_brand', 'brand_code'),
        Index('idx_sku_sequence_category', 'category_code'),
    )
    
    def __init__(
        self,
        brand_code: Optional[str] = None,
        category_code: Optional[str] = None,
        next_sequence: str = "1",
        **kwargs
    ):
        """
        Initialize a SKU Sequence.
        
        Args:
            brand_code: Brand code for SKU generation
            category_code: Category code for SKU generation  
            next_sequence: Next sequence number
            **kwargs: Additional BaseModel fields
        """
        super().__init__(**kwargs)
        self.brand_code = brand_code
        self.category_code = category_code
        self.next_sequence = next_sequence
        self._validate()
    
    def _validate(self):
        """Validate SKU sequence business rules."""
        # Brand code validation
        if self.brand_code:
            if len(self.brand_code) > 20:
                raise ValueError("Brand code cannot exceed 20 characters")
            self.brand_code = self.brand_code.upper().strip()
        
        # Category code validation
        if self.category_code:
            if len(self.category_code) > 20:
                raise ValueError("Category code cannot exceed 20 characters")
            self.category_code = self.category_code.upper().strip()
        
        # Sequence validation
        try:
            int(self.next_sequence)
        except ValueError:
            raise ValueError("Next sequence must be a valid number")
    
    def get_next_sequence_number(self) -> int:
        """Get next sequence number as integer."""
        return int(self.next_sequence)
    
    def increment_sequence(self):
        """Increment the sequence number."""
        current = int(self.next_sequence)
        self.next_sequence = str(current + 1)
    
    @property
    def sequence_key(self) -> str:
        """Get unique key for this sequence."""
        return f"{self.brand_code or 'NONE'}-{self.category_code or 'NONE'}"
    
    def __str__(self) -> str:
        """String representation of SKU sequence."""
        return f"SKU Sequence: {self.sequence_key} -> {self.next_sequence}"
    
    def __repr__(self) -> str:
        """Developer representation of SKU sequence."""
        return (
            f"SKUSequence(id={self.id}, brand_code='{self.brand_code}', "
            f"category_code='{self.category_code}', next_sequence='{self.next_sequence}')"
        )


class StockMovement(Base, TimestampMixin, AuditMixin):
    """
    Stock movement model for tracking all stock changes with audit trail.
    
    This model records every change to stock levels, including the type of movement,
    quantities before and after, and references to the triggering transactions.
    Stock movements are immutable audit records and do not support soft deletion.
    
    Attributes:
        id: Primary key UUID
        stock_level_id: Reference to the stock level being modified
        item_id: Item ID for efficient querying
        location_id: Location ID for efficient querying
        movement_type: Type of movement (PURCHASE, SALE, RENTAL_OUT, etc.)
        reference_type: Type of reference (TRANSACTION, MANUAL_ADJUSTMENT, etc.)
        reference_id: External reference ID (transaction ID, etc.)
        quantity_change: Quantity change (positive for additions, negative for reductions)
        quantity_before: Quantity before the movement
        quantity_after: Quantity after the movement
        reason: Human-readable reason for the movement
        notes: Additional notes
        transaction_line_id: Optional link to specific transaction line
        is_active: Active status (for compatibility, always True for movements)
        stock_level: Relationship to stock level
        item: Relationship to item
    """
    
    __tablename__ = "stock_movements"
    
    # Primary key
    id = Column(UUIDType(), primary_key=True, default=uuid4, comment="Primary key UUID")
    
    # Core references
    stock_level_id = Column(UUIDType(), ForeignKey("stock_levels.id"), nullable=False, comment="Stock level ID")
    item_id = Column(UUIDType(), ForeignKey("items.id"), nullable=False, comment="Item ID")
    location_id = Column(UUIDType(), ForeignKey("locations.id"), nullable=False, comment="Location ID")
    
    # Active status for compatibility
    is_active = Column(Boolean, nullable=False, default=True, comment="Active status")
    
    # Movement classification
    movement_type = Column(String(50), nullable=False, comment="Type of movement")
    reference_type = Column(String(50), nullable=False, comment="Type of reference")
    reference_id = Column(String(100), nullable=True, comment="External reference ID")
    
    # Quantity tracking
    quantity_change = Column(Numeric(10, 2), nullable=False, comment="Quantity change (+/-)")
    quantity_before = Column(Numeric(10, 2), nullable=False, comment="Quantity before movement")
    quantity_after = Column(Numeric(10, 2), nullable=False, comment="Quantity after movement")
    
    # Context and audit
    reason = Column(String(500), nullable=False, comment="Reason for movement")
    notes = Column(Text, nullable=True, comment="Additional notes")
    transaction_line_id = Column(UUIDType(), nullable=True, comment="Transaction line reference")
    
    # Relationships
    stock_level = relationship("StockLevel", back_populates="stock_movements", lazy="select")
    item = relationship("Item", back_populates="stock_movements", lazy="select")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_stock_movement_stock_level', 'stock_level_id'),
        Index('idx_stock_movement_item', 'item_id'),
        Index('idx_stock_movement_location', 'location_id'),
        Index('idx_stock_movement_type', 'movement_type'),
        Index('idx_stock_movement_reference', 'reference_type', 'reference_id'),
        Index('idx_stock_movement_created', 'created_at'),
        Index('idx_stock_movement_item_created', 'item_id', 'created_at'),
        Index('idx_stock_movement_stock_created', 'stock_level_id', 'created_at'),
    )
    
    def __init__(
        self,
        stock_level_id: str,
        item_id: str,
        location_id: str,
        movement_type: MovementType,
        reference_type: ReferenceType,
        quantity_change: Decimal,
        quantity_before: Decimal,
        quantity_after: Decimal,
        reason: str,
        reference_id: Optional[str] = None,
        notes: Optional[str] = None,
        transaction_line_id: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize a Stock Movement.
        
        Args:
            stock_level_id: Stock level ID
            item_id: Item ID
            location_id: Location ID
            movement_type: Type of movement
            reference_type: Type of reference
            quantity_change: Quantity change (+/-)
            quantity_before: Quantity before movement
            quantity_after: Quantity after movement
            reason: Reason for movement
            reference_id: External reference ID
            notes: Additional notes
            transaction_line_id: Transaction line reference
            **kwargs: Additional BaseModel fields
        """
        super().__init__(**kwargs)
        self.stock_level_id = stock_level_id
        self.item_id = item_id
        self.location_id = location_id
        self.movement_type = movement_type.value if isinstance(movement_type, MovementType) else movement_type
        self.reference_type = reference_type.value if isinstance(reference_type, ReferenceType) else reference_type
        self.quantity_change = quantity_change
        self.quantity_before = quantity_before
        self.quantity_after = quantity_after
        self.reason = reason
        self.reference_id = reference_id
        self.notes = notes
        self.transaction_line_id = transaction_line_id
        self._validate()
    
    def _validate(self):
        """Validate stock movement business rules."""
        # Movement type validation
        if self.movement_type not in [mt.value for mt in MovementType]:
            raise ValueError(f"Invalid movement type: {self.movement_type}")
        
        # Reference type validation
        if self.reference_type not in [rt.value for rt in ReferenceType]:
            raise ValueError(f"Invalid reference type: {self.reference_type}")
        
        # Quantity validation
        if self.quantity_before < 0:
            raise ValueError("Quantity before cannot be negative")
        
        if self.quantity_after < 0:
            raise ValueError("Quantity after cannot be negative")
        
        # Validate quantity math
        calculated_after = self.quantity_before + self.quantity_change
        if abs(calculated_after - self.quantity_after) > Decimal('0.01'):
            raise ValueError("Quantity math doesn't add up: before + change != after")
        
        # Reason validation
        if not self.reason or not self.reason.strip():
            raise ValueError("Reason cannot be empty")
        
        if len(self.reason) > 500:
            raise ValueError("Reason cannot exceed 500 characters")
        
        # Reference ID validation
        if self.reference_id and len(self.reference_id) > 100:
            raise ValueError("Reference ID cannot exceed 100 characters")
    
    def is_increase(self) -> bool:
        """Check if this movement increases stock."""
        return self.quantity_change > 0
    
    def is_decrease(self) -> bool:
        """Check if this movement decreases stock."""
        return self.quantity_change < 0
    
    def is_neutral(self) -> bool:
        """Check if this movement is neutral (no change)."""
        return self.quantity_change == 0
    
    @property
    def display_name(self) -> str:
        """Get movement display name."""
        direction = "+" if self.quantity_change >= 0 else ""
        return f"{self.movement_type}: {direction}{self.quantity_change}"
    
    @property
    def full_display_name(self) -> str:
        """Get full movement display name with item info."""
        if self.item:
            return f"{self.item.item_name} - {self.display_name}"
        return self.display_name
    
    def __str__(self) -> str:
        """String representation of stock movement."""
        return self.full_display_name
    
    def __repr__(self) -> str:
        """Developer representation of stock movement."""
        return (
            f"StockMovement(id={self.id}, type='{self.movement_type}', "
            f"change={self.quantity_change}, before={self.quantity_before}, "
            f"after={self.quantity_after}, active={self.is_active})"
        )