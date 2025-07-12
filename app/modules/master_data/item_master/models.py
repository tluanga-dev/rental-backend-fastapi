from enum import Enum
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
from sqlalchemy import Column, String, Numeric, Boolean, Text, ForeignKey, Index
from sqlalchemy.orm import relationship, validates

from app.db.base import BaseModel, UUIDType

if TYPE_CHECKING:
    from app.modules.master_data.brands.models import Brand
    from app.modules.master_data.categories.models import Category
    from app.modules.master_data.units.models import UnitOfMeasurement
    from app.modules.inventory.models import InventoryUnit, StockLevel
    from app.modules.transactions.models import TransactionLine


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


class Item(BaseModel):
    """
    Item model for master data management.
    
    Attributes:
        item_code: Unique item code
        sku: Stock Keeping Unit
        item_name: Item name
        item_type: Type of item (RENTAL, SALE, BOTH)
        item_status: Status of item (ACTIVE, INACTIVE, DISCONTINUED)
        brand_id: Brand ID
        category_id: Category ID
        unit_of_measurement_id: Unit of measurement ID
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
        is_rentable: Item can be rented (default: True)
        is_saleable: Item can be sold (default: False)
        brand: Brand relationship
        category: Category relationship
        unit_of_measurement: Unit of measurement relationship
        inventory_units: Inventory units
        stock_levels: Stock levels
        
    Note:
        is_rentable and is_saleable are mutually exclusive - both cannot be True at the same time.
    """
    
    __tablename__ = "items"
    
    item_code = Column(String(50), nullable=False, unique=True, index=True, comment="Unique item code")
    sku = Column(String(50), nullable=False, unique=True, index=True, comment="Stock Keeping Unit")
    item_name = Column(String(200), nullable=False, comment="Item name")
    item_type = Column(String(20), nullable=False, comment="Item type")
    item_status = Column(String(20), nullable=False, default=ItemStatus.ACTIVE.value, comment="Item status")
    brand_id = Column(UUIDType(), ForeignKey("brands.id"), nullable=True, comment="Brand ID")
    category_id = Column(UUIDType(), ForeignKey("categories.id"), nullable=True, comment="Category ID")
    unit_of_measurement_id = Column(UUIDType(), ForeignKey("units_of_measurement.id"), nullable=False, comment="Unit of measurement ID")
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
    is_rentable = Column(Boolean, nullable=False, default=True, comment="Item can be rented")
    is_saleable = Column(Boolean, nullable=False, default=False, comment="Item can be sold")
    
    # Relationships - re-enabled with proper foreign keys
    brand = relationship("Brand", back_populates="items", lazy="select")
    category = relationship("Category", back_populates="items", lazy="select")
    unit_of_measurement = relationship("UnitOfMeasurement", back_populates="items", lazy="select")
    inventory_units = relationship("InventoryUnit", back_populates="item", lazy="select")
    stock_levels = relationship("StockLevel", back_populates="item", lazy="select")
    transaction_lines = relationship("TransactionLine", back_populates="item", lazy="select")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_item_code', 'item_code'),
        Index('idx_item_sku', 'sku'),
        Index('idx_item_name', 'item_name'),
        Index('idx_item_type', 'item_type'),
        Index('idx_item_status', 'item_status'),
        Index('idx_item_brand', 'brand_id'),
        Index('idx_item_category', 'category_id'),
    )
    
    def __init__(
        self,
        item_code: str,
        sku: str,
        item_name: str,
        item_type: ItemType,
        item_status: ItemStatus = ItemStatus.ACTIVE,
        is_rentable: bool = True,
        is_saleable: bool = False,
        **kwargs
    ):
        """
        Initialize an Item.
        
        Args:
            item_code: Unique item code
            sku: Stock Keeping Unit
            item_name: Item name
            item_type: Type of item
            item_status: Status of item
            is_rentable: Item can be rented (default: True)
            is_saleable: Item can be sold (default: False)
            **kwargs: Additional BaseModel fields
        """
        super().__init__(**kwargs)
        self.item_code = item_code
        self.sku = sku
        self.item_name = item_name
        self.item_type = item_type.value if isinstance(item_type, ItemType) else item_type
        self.item_status = item_status.value if isinstance(item_status, ItemStatus) else item_status
        self.is_rentable = is_rentable
        self.is_saleable = is_saleable
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
        
        # Boolean field validation
        if hasattr(self, 'is_rentable') and hasattr(self, 'is_saleable'):
            if self.is_rentable and self.is_saleable:
                raise ValueError("Item cannot be both rentable and saleable - these are mutually exclusive")
            if not self.is_rentable and not self.is_saleable:
                raise ValueError("Item must be either rentable or saleable")
        
        # Price validation
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
    
    @validates('item_type')
    def validate_item_type_pricing(self, key, value):
        """Validate that required pricing is present based on item type."""
        if value == ItemType.RENTAL.value and not self.rental_price_per_day:
            raise ValueError("Rental items must have rental_price_per_day")
        elif value == ItemType.SALE.value and not self.sale_price:
            raise ValueError("Sale items must have sale_price")
        elif value == ItemType.BOTH.value and (not self.rental_price_per_day or not self.sale_price):
            raise ValueError("Items with type BOTH must have both rental_price_per_day and sale_price")
        return value
    
    def is_rental_item(self) -> bool:
        """Check if item is available for rental."""
        # Prioritize new boolean field if available, fallback to item_type for backward compatibility
        if hasattr(self, 'is_rentable'):
            return self.is_rentable
        return self.item_type in [ItemType.RENTAL.value, ItemType.BOTH.value]
    
    def is_sale_item(self) -> bool:
        """Check if item is available for sale."""
        # Prioritize new boolean field if available, fallback to item_type for backward compatibility
        if hasattr(self, 'is_saleable'):
            return self.is_saleable
        return self.item_type in [ItemType.SALE.value, ItemType.BOTH.value]
    
    def is_item_active(self) -> bool:
        """Check if item is active."""
        return self.item_status == ItemStatus.ACTIVE.value and super().is_active
    
    def is_discontinued(self) -> bool:
        """Check if item is discontinued."""
        return self.item_status == ItemStatus.DISCONTINUED.value
    
    def can_be_rented(self) -> bool:
        """Check if item can be rented."""
        return self.is_rental_item() and self.is_item_active() and self.rental_price_per_day
    
    def can_be_sold(self) -> bool:
        """Check if item can be sold."""
        return self.is_sale_item() and self.is_item_active() and self.sale_price
    
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
        from app.modules.inventory.models import InventoryUnitStatus
        return len([unit for unit in self.inventory_units if unit.status == InventoryUnitStatus.AVAILABLE.value])
    
    @property
    def rented_units(self) -> int:
        """Get number of rented inventory units."""
        if not self.inventory_units:
            return 0
        from app.modules.inventory.models import InventoryUnitStatus
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