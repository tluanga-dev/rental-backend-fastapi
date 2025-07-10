from enum import Enum
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
from datetime import datetime
from sqlalchemy import Column, String, Numeric, Boolean, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

from app.db.base import BaseModel, UUIDType

if TYPE_CHECKING:
    from app.modules.master_data.brands.models import Brand
    from app.modules.master_data.categories.models import Category
    from app.modules.master_data.units.models import UnitOfMeasurement
    from app.modules.master_data.locations.models import Location
    from app.modules.suppliers.models import Supplier


class ItemType(str, Enum):
    """Item type enumeration."""
    RENTAL = "RENTAL"
    SALE = "SALE"
    BOTH = "BOTH"


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


class Item(BaseModel):
    """
    Item model for inventory management.
    
    Attributes:
        item_code: Unique item code
        item_name: Item name
        item_type: Type of item (RENTAL, SALE, BOTH)
        item_status: Status of item (ACTIVE, INACTIVE, DISCONTINUED)
        brand_id: Brand ID
        category_id: Category ID
        unit_of_measurement_id: Unit of measurement ID
        supplier_id: Default supplier ID
        purchase_price: Purchase price
        rental_price_per_day: Rental price per day
        rental_price_per_week: Rental price per week
        rental_price_per_month: Rental price per month
        sale_price: Sale price
        minimum_rental_days: Minimum rental days
        maximum_rental_days: Maximum rental days
        security_deposit: Security deposit amount
        description: Item description
        specifications: Item specifications
        model_number: Model number
        serial_number_required: Whether serial number is required
        warranty_period_days: Warranty period in days
        reorder_level: Reorder level
        reorder_quantity: Reorder quantity
        brand: Brand relationship
        category: Category relationship
        unit_of_measurement: Unit of measurement relationship
        supplier: Supplier relationship
        inventory_units: Inventory units
        stock_levels: Stock levels
    """
    
    __tablename__ = "items"
    
    item_code = Column(String(50), nullable=False, unique=True, index=True, comment="Unique item code")
    item_name = Column(String(200), nullable=False, comment="Item name")
    item_type = Column(String(20), nullable=False, comment="Item type")
    item_status = Column(String(20), nullable=False, default=ItemStatus.ACTIVE.value, comment="Item status")
    brand_id = Column(UUIDType(), ForeignKey("brands.id"), nullable=True, comment="Brand ID")
    category_id = Column(UUIDType(), ForeignKey("categories.id"), nullable=True, comment="Category ID")
    unit_of_measurement_id = Column(UUIDType(), nullable=True, comment="Unit of measurement ID")  # ForeignKey("units_of_measurement.id") - temporarily disabled
    supplier_id = Column(UUIDType(), nullable=True, comment="Default supplier ID")  # ForeignKey("suppliers.id") - temporarily disabled
    purchase_price = Column(Numeric(10, 2), nullable=False, default=0.00, comment="Purchase price")
    rental_price_per_day = Column(Numeric(10, 2), nullable=True, comment="Rental price per day")
    rental_price_per_week = Column(Numeric(10, 2), nullable=True, comment="Rental price per week")
    rental_price_per_month = Column(Numeric(10, 2), nullable=True, comment="Rental price per month")
    sale_price = Column(Numeric(10, 2), nullable=True, comment="Sale price")
    minimum_rental_days = Column(String(10), nullable=True, comment="Minimum rental days")
    maximum_rental_days = Column(String(10), nullable=True, comment="Maximum rental days")
    security_deposit = Column(Numeric(10, 2), nullable=False, default=0.00, comment="Security deposit")
    description = Column(Text, nullable=True, comment="Item description")
    specifications = Column(Text, nullable=True, comment="Item specifications")
    model_number = Column(String(100), nullable=True, comment="Model number")
    serial_number_required = Column(Boolean, nullable=False, default=False, comment="Serial number required")
    warranty_period_days = Column(String(10), nullable=False, default="0", comment="Warranty period in days")
    reorder_level = Column(String(10), nullable=False, default="0", comment="Reorder level")
    reorder_quantity = Column(String(10), nullable=False, default="0", comment="Reorder quantity")
    
    # Relationships
    # brand = relationship("Brand", back_populates="items", lazy="select")  # Temporarily disabled
    # category = relationship("Category", back_populates="items", lazy="select")  # Temporarily disabled
    # unit_of_measurement = relationship("UnitOfMeasurement", back_populates="items", lazy="select")  # Temporarily disabled
    # supplier = relationship("Supplier", back_populates="items", lazy="select")  # Temporarily disabled
    inventory_units = relationship("InventoryUnit", back_populates="item", lazy="select")
    stock_levels = relationship("StockLevel", back_populates="item", lazy="select")
    # transaction_lines = relationship("TransactionLine", back_populates="item", lazy="select")  # Temporarily disabled
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_item_code', 'item_code'),
        Index('idx_item_name', 'item_name'),
        Index('idx_item_type', 'item_type'),
        Index('idx_item_status', 'item_status'),
        Index('idx_item_brand', 'brand_id'),
        Index('idx_item_category', 'category_id'),
        Index('idx_item_supplier', 'supplier_id'),
    )
    
    def __init__(
        self,
        item_code: str,
        item_name: str,
        item_type: ItemType,
        purchase_price: Decimal = Decimal("0.00"),
        item_status: ItemStatus = ItemStatus.ACTIVE,
        **kwargs
    ):
        """
        Initialize an Item.
        
        Args:
            item_code: Unique item code
            item_name: Item name
            item_type: Type of item
            purchase_price: Purchase price
            item_status: Status of item
            **kwargs: Additional BaseModel fields
        """
        super().__init__(**kwargs)
        self.item_code = item_code
        self.item_name = item_name
        self.item_type = item_type.value if isinstance(item_type, ItemType) else item_type
        self.purchase_price = purchase_price
        self.item_status = item_status.value if isinstance(item_status, ItemStatus) else item_status
        self.security_deposit = Decimal("0.00")
        self.warranty_period_days = "0"
        self.reorder_level = "0"
        self.reorder_quantity = "0"
        self._validate()
    
    def _validate(self):
        """Validate item business rules."""
        # Code validation
        if not self.item_code or not self.item_code.strip():
            raise ValueError("Item code cannot be empty")
        
        if len(self.item_code) > 50:
            raise ValueError("Item code cannot exceed 50 characters")
        
        # Name validation
        if not self.item_name or not self.item_name.strip():
            raise ValueError("Item name cannot be empty")
        
        if len(self.item_name) > 200:
            raise ValueError("Item name cannot exceed 200 characters")
        
        # Type validation
        if self.item_type not in [it.value for it in ItemType]:
            raise ValueError(f"Invalid item type: {self.item_type}")
        
        # Status validation
        if self.item_status not in [status.value for status in ItemStatus]:
            raise ValueError(f"Invalid item status: {self.item_status}")
        
        # Price validation
        if self.purchase_price < 0:
            raise ValueError("Purchase price cannot be negative")
        
        if self.rental_price_per_day and self.rental_price_per_day < 0:
            raise ValueError("Rental price per day cannot be negative")
        
        if self.rental_price_per_week and self.rental_price_per_week < 0:
            raise ValueError("Rental price per week cannot be negative")
        
        if self.rental_price_per_month and self.rental_price_per_month < 0:
            raise ValueError("Rental price per month cannot be negative")
        
        if self.sale_price and self.sale_price < 0:
            raise ValueError("Sale price cannot be negative")
        
        if self.security_deposit < 0:
            raise ValueError("Security deposit cannot be negative")
        
        # Rental days validation
        if self.minimum_rental_days:
            try:
                min_days = int(self.minimum_rental_days)
                if min_days < 0:
                    raise ValueError("Minimum rental days cannot be negative")
            except ValueError:
                raise ValueError("Minimum rental days must be a valid number")
        
        if self.maximum_rental_days:
            try:
                max_days = int(self.maximum_rental_days)
                if max_days < 0:
                    raise ValueError("Maximum rental days cannot be negative")
                if self.minimum_rental_days and max_days < int(self.minimum_rental_days):
                    raise ValueError("Maximum rental days cannot be less than minimum rental days")
            except ValueError:
                raise ValueError("Maximum rental days must be a valid number")
    
    def is_rental_item(self) -> bool:
        """Check if item is available for rental."""
        return self.item_type in [ItemType.RENTAL.value, ItemType.BOTH.value]
    
    def is_sale_item(self) -> bool:
        """Check if item is available for sale."""
        return self.item_type in [ItemType.SALE.value, ItemType.BOTH.value]
    
    def is_active(self) -> bool:
        """Check if item is active."""
        return self.item_status == ItemStatus.ACTIVE.value and self.is_active
    
    def is_discontinued(self) -> bool:
        """Check if item is discontinued."""
        return self.item_status == ItemStatus.DISCONTINUED.value
    
    def can_be_rented(self) -> bool:
        """Check if item can be rented."""
        return self.is_rental_item() and self.is_active() and self.rental_price_per_day
    
    def can_be_sold(self) -> bool:
        """Check if item can be sold."""
        return self.is_sale_item() and self.is_active() and self.sale_price
    
    @property
    def display_name(self) -> str:
        """Get item display name."""
        return f"{self.item_name} ({self.item_code})"
    
    @property
    def total_inventory_units(self) -> int:
        """Get total number of inventory units."""
        return len(self.inventory_units) if self.inventory_units else 0
    
    @property
    def available_units(self) -> int:
        """Get number of available inventory units."""
        if not self.inventory_units:
            return 0
        return len([unit for unit in self.inventory_units if unit.status == InventoryUnitStatus.AVAILABLE.value])
    
    @property
    def rented_units(self) -> int:
        """Get number of rented inventory units."""
        if not self.inventory_units:
            return 0
        return len([unit for unit in self.inventory_units if unit.status == InventoryUnitStatus.RENTED.value])
    
    def __str__(self) -> str:
        """String representation of item."""
        return self.display_name
    
    def __repr__(self) -> str:
        """Developer representation of item."""
        return (
            f"Item(id={self.id}, code='{self.item_code}', "
            f"name='{self.item_name}', type='{self.item_type}', "
            f"status='{self.item_status}', active={self.is_active})"
        )


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
    # return_lines = relationship("RentalReturnLine", back_populates="inventory_unit", lazy="select")  # Temporarily disabled
    # inspection_reports = relationship("InspectionReport", back_populates="inventory_unit", lazy="select")  # Temporarily disabled
    
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
    
    Attributes:
        item_id: Item ID
        location_id: Location ID
        quantity_on_hand: Current quantity on hand
        quantity_available: Available quantity
        quantity_reserved: Reserved quantity
        quantity_on_order: Quantity on order
        minimum_level: Minimum stock level
        maximum_level: Maximum stock level
        reorder_point: Reorder point
        item: Item relationship
        location: Location relationship
    """
    
    __tablename__ = "stock_levels"
    
    item_id = Column(UUIDType(), ForeignKey("items.id"), nullable=False, comment="Item ID")
    location_id = Column(UUIDType(), ForeignKey("locations.id"), nullable=False, comment="Location ID")
    quantity_on_hand = Column(String(10), nullable=False, default="0", comment="Current quantity on hand")
    quantity_available = Column(String(10), nullable=False, default="0", comment="Available quantity")
    quantity_reserved = Column(String(10), nullable=False, default="0", comment="Reserved quantity")
    quantity_on_order = Column(String(10), nullable=False, default="0", comment="Quantity on order")
    minimum_level = Column(String(10), nullable=False, default="0", comment="Minimum stock level")
    maximum_level = Column(String(10), nullable=False, default="0", comment="Maximum stock level")
    reorder_point = Column(String(10), nullable=False, default="0", comment="Reorder point")
    
    # Relationships
    item = relationship("Item", back_populates="stock_levels", lazy="select")
    # location = relationship("Location", back_populates="stock_levels", lazy="select")  # Temporarily disabled
    
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
        quantity_on_hand: str = "0",
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
        self.quantity_reserved = "0"
        self.quantity_on_order = "0"
        self.minimum_level = "0"
        self.maximum_level = "0"
        self.reorder_point = "0"
        self._validate()
    
    def _validate(self):
        """Validate stock level business rules."""
        # Validate all quantities are valid numbers
        try:
            int(self.quantity_on_hand)
            int(self.quantity_available)
            int(self.quantity_reserved)
            int(self.quantity_on_order)
            int(self.minimum_level)
            int(self.maximum_level)
            int(self.reorder_point)
        except ValueError:
            raise ValueError("All quantity fields must be valid numbers")
        
        # Validate non-negative quantities
        if int(self.quantity_on_hand) < 0:
            raise ValueError("Quantity on hand cannot be negative")
        
        if int(self.quantity_available) < 0:
            raise ValueError("Available quantity cannot be negative")
        
        if int(self.quantity_reserved) < 0:
            raise ValueError("Reserved quantity cannot be negative")
        
        if int(self.quantity_on_order) < 0:
            raise ValueError("Quantity on order cannot be negative")
        
        if int(self.minimum_level) < 0:
            raise ValueError("Minimum level cannot be negative")
        
        if int(self.maximum_level) < 0:
            raise ValueError("Maximum level cannot be negative")
        
        if int(self.reorder_point) < 0:
            raise ValueError("Reorder point cannot be negative")
    
    def is_below_minimum(self) -> bool:
        """Check if stock is below minimum level."""
        return int(self.quantity_on_hand) < int(self.minimum_level)
    
    def is_above_maximum(self) -> bool:
        """Check if stock is above maximum level."""
        return int(self.quantity_on_hand) > int(self.maximum_level)
    
    def needs_reorder(self) -> bool:
        """Check if stock needs reordering."""
        return int(self.quantity_on_hand) <= int(self.reorder_point)
    
    def adjust_quantity(self, adjustment: int, updated_by: Optional[str] = None):
        """Adjust quantity on hand."""
        current_quantity = int(self.quantity_on_hand)
        new_quantity = current_quantity + adjustment
        
        if new_quantity < 0:
            raise ValueError("Quantity adjustment would result in negative stock")
        
        self.quantity_on_hand = str(new_quantity)
        self.quantity_available = str(max(0, new_quantity - int(self.quantity_reserved)))
        self.updated_by = updated_by
    
    def reserve_quantity(self, quantity: int, updated_by: Optional[str] = None):
        """Reserve quantity."""
        if quantity < 0:
            raise ValueError("Cannot reserve negative quantity")
        
        available_quantity = int(self.quantity_available)
        if quantity > available_quantity:
            raise ValueError("Cannot reserve more than available quantity")
        
        self.quantity_reserved = str(int(self.quantity_reserved) + quantity)
        self.quantity_available = str(int(self.quantity_available) - quantity)
        self.updated_by = updated_by
    
    def release_reservation(self, quantity: int, updated_by: Optional[str] = None):
        """Release reserved quantity."""
        if quantity < 0:
            raise ValueError("Cannot release negative quantity")
        
        reserved_quantity = int(self.quantity_reserved)
        if quantity > reserved_quantity:
            raise ValueError("Cannot release more than reserved quantity")
        
        self.quantity_reserved = str(reserved_quantity - quantity)
        self.quantity_available = str(int(self.quantity_available) + quantity)
        self.updated_by = updated_by
    
    @property
    def display_name(self) -> str:
        """Get stock level display name."""
        if self.item and self.location:
            return f"{self.item.item_name} @ {self.location.location_name}"
        return f"Stock Level {self.id}"
    
    def __str__(self) -> str:
        """String representation of stock level."""
        return self.display_name
    
    def __repr__(self) -> str:
        """Developer representation of stock level."""
        return (
            f"StockLevel(id={self.id}, item_id={self.item_id}, "
            f"location_id={self.location_id}, on_hand={self.quantity_on_hand}, "
            f"available={self.quantity_available}, active={self.is_active})"
        )