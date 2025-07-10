from typing import Optional, List, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator, computed_field
from uuid import UUID

from app.modules.inventory.models import ItemType, ItemStatus, InventoryUnitStatus, InventoryUnitCondition


class ItemCreate(BaseModel):
    """Schema for creating a new item."""
    model_config = ConfigDict(protected_namespaces=())
    
    item_code: str = Field(..., max_length=50, description="Unique item code")
    item_name: str = Field(..., max_length=200, description="Item name")
    item_type: ItemType = Field(..., description="Item type")
    item_status: ItemStatus = Field(default=ItemStatus.ACTIVE, description="Item status")
    brand_id: Optional[UUID] = Field(None, description="Brand ID")
    category_id: Optional[UUID] = Field(None, description="Category ID")
    unit_of_measurement_id: Optional[UUID] = Field(None, description="Unit of measurement ID")
    supplier_id: Optional[UUID] = Field(None, description="Default supplier ID")
    purchase_price: Decimal = Field(default=Decimal("0.00"), ge=0, description="Purchase price")
    rental_price_per_day: Optional[Decimal] = Field(None, ge=0, description="Rental price per day")
    rental_price_per_week: Optional[Decimal] = Field(None, ge=0, description="Rental price per week")
    rental_price_per_month: Optional[Decimal] = Field(None, ge=0, description="Rental price per month")
    sale_price: Optional[Decimal] = Field(None, ge=0, description="Sale price")
    minimum_rental_days: Optional[str] = Field(None, description="Minimum rental days")
    maximum_rental_days: Optional[str] = Field(None, description="Maximum rental days")
    security_deposit: Decimal = Field(default=Decimal("0.00"), ge=0, description="Security deposit")
    description: Optional[str] = Field(None, description="Item description")
    specifications: Optional[str] = Field(None, description="Item specifications")
    model_number: Optional[str] = Field(None, max_length=100, description="Model number")
    serial_number_required: bool = Field(default=False, description="Serial number required")
    warranty_period_days: str = Field(default="0", description="Warranty period in days")
    reorder_level: str = Field(default="0", description="Reorder level")
    reorder_quantity: str = Field(default="0", description="Reorder quantity")
    
    @field_validator('minimum_rental_days', 'maximum_rental_days', 'warranty_period_days', 'reorder_level', 'reorder_quantity')
    @classmethod
    def validate_numeric_string(cls, v):
        if v is not None and v != "":
            try:
                int(v)
            except ValueError:
                raise ValueError("Must be a valid number")
        return v
    
    @field_validator('maximum_rental_days')
    @classmethod
    def validate_max_rental_days(cls, v, info):
        if v is not None and info.data.get('minimum_rental_days') is not None:
            try:
                min_days = int(info.data.get('minimum_rental_days'))
                max_days = int(v)
                if max_days < min_days:
                    raise ValueError("Maximum rental days cannot be less than minimum rental days")
            except ValueError:
                pass
        return v


class ItemUpdate(BaseModel):
    """Schema for updating an item."""
    model_config = ConfigDict(protected_namespaces=())
    
    item_name: Optional[str] = Field(None, max_length=200, description="Item name")
    item_type: Optional[ItemType] = Field(None, description="Item type")
    item_status: Optional[ItemStatus] = Field(None, description="Item status")
    brand_id: Optional[UUID] = Field(None, description="Brand ID")
    category_id: Optional[UUID] = Field(None, description="Category ID")
    unit_of_measurement_id: Optional[UUID] = Field(None, description="Unit of measurement ID")
    supplier_id: Optional[UUID] = Field(None, description="Default supplier ID")
    purchase_price: Optional[Decimal] = Field(None, ge=0, description="Purchase price")
    rental_price_per_day: Optional[Decimal] = Field(None, ge=0, description="Rental price per day")
    rental_price_per_week: Optional[Decimal] = Field(None, ge=0, description="Rental price per week")
    rental_price_per_month: Optional[Decimal] = Field(None, ge=0, description="Rental price per month")
    sale_price: Optional[Decimal] = Field(None, ge=0, description="Sale price")
    minimum_rental_days: Optional[str] = Field(None, description="Minimum rental days")
    maximum_rental_days: Optional[str] = Field(None, description="Maximum rental days")
    security_deposit: Optional[Decimal] = Field(None, ge=0, description="Security deposit")
    description: Optional[str] = Field(None, description="Item description")
    specifications: Optional[str] = Field(None, description="Item specifications")
    model_number: Optional[str] = Field(None, max_length=100, description="Model number")
    serial_number_required: Optional[bool] = Field(None, description="Serial number required")
    warranty_period_days: Optional[str] = Field(None, description="Warranty period in days")
    reorder_level: Optional[str] = Field(None, description="Reorder level")
    reorder_quantity: Optional[str] = Field(None, description="Reorder quantity")
    
    @field_validator('minimum_rental_days', 'maximum_rental_days', 'warranty_period_days', 'reorder_level', 'reorder_quantity')
    @classmethod
    def validate_numeric_string(cls, v):
        if v is not None and v != "":
            try:
                int(v)
            except ValueError:
                raise ValueError("Must be a valid number")
        return v


class ItemResponse(BaseModel):
    """Schema for item response."""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    
    id: UUID
    item_code: str
    item_name: str
    item_type: ItemType
    item_status: ItemStatus
    brand_id: Optional[UUID]
    category_id: Optional[UUID]
    unit_of_measurement_id: Optional[UUID]
    supplier_id: Optional[UUID]
    purchase_price: Decimal
    rental_price_per_day: Optional[Decimal]
    rental_price_per_week: Optional[Decimal]
    rental_price_per_month: Optional[Decimal]
    sale_price: Optional[Decimal]
    minimum_rental_days: Optional[str]
    maximum_rental_days: Optional[str]
    security_deposit: Decimal
    description: Optional[str]
    specifications: Optional[str]
    model_number: Optional[str]
    serial_number_required: bool
    warranty_period_days: str
    reorder_level: str
    reorder_quantity: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def display_name(self) -> str:
        return f"{self.item_name} ({self.item_code})"
    
    @computed_field
    @property
    def is_rental_item(self) -> bool:
        return self.item_type in [ItemType.RENTAL, ItemType.BOTH]
    
    @computed_field
    @property
    def is_sale_item(self) -> bool:
        return self.item_type in [ItemType.SALE, ItemType.BOTH]


class ItemListResponse(BaseModel):
    """Schema for item list response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    item_code: str
    item_name: str
    item_type: ItemType
    item_status: ItemStatus
    purchase_price: Decimal
    rental_price_per_day: Optional[Decimal]
    sale_price: Optional[Decimal]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def display_name(self) -> str:
        return f"{self.item_name} ({self.item_code})"


class InventoryUnitCreate(BaseModel):
    """Schema for creating a new inventory unit."""
    item_id: UUID = Field(..., description="Item ID")
    location_id: UUID = Field(..., description="Location ID")
    unit_code: str = Field(..., max_length=50, description="Unique unit code")
    serial_number: Optional[str] = Field(None, max_length=100, description="Serial number")
    status: InventoryUnitStatus = Field(default=InventoryUnitStatus.AVAILABLE, description="Unit status")
    condition: InventoryUnitCondition = Field(default=InventoryUnitCondition.NEW, description="Unit condition")
    purchase_date: Optional[datetime] = Field(None, description="Purchase date")
    purchase_price: Decimal = Field(default=Decimal("0.00"), ge=0, description="Purchase price")
    warranty_expiry: Optional[datetime] = Field(None, description="Warranty expiry date")
    notes: Optional[str] = Field(None, description="Additional notes")


class InventoryUnitUpdate(BaseModel):
    """Schema for updating an inventory unit."""
    location_id: Optional[UUID] = Field(None, description="Location ID")
    serial_number: Optional[str] = Field(None, max_length=100, description="Serial number")
    status: Optional[InventoryUnitStatus] = Field(None, description="Unit status")
    condition: Optional[InventoryUnitCondition] = Field(None, description="Unit condition")
    purchase_date: Optional[datetime] = Field(None, description="Purchase date")
    purchase_price: Optional[Decimal] = Field(None, ge=0, description="Purchase price")
    warranty_expiry: Optional[datetime] = Field(None, description="Warranty expiry date")
    last_maintenance_date: Optional[datetime] = Field(None, description="Last maintenance date")
    next_maintenance_date: Optional[datetime] = Field(None, description="Next maintenance date")
    notes: Optional[str] = Field(None, description="Additional notes")


class InventoryUnitResponse(BaseModel):
    """Schema for inventory unit response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    item_id: UUID
    location_id: UUID
    unit_code: str
    serial_number: Optional[str]
    status: InventoryUnitStatus
    condition: InventoryUnitCondition
    purchase_date: Optional[datetime]
    purchase_price: Decimal
    warranty_expiry: Optional[datetime]
    last_maintenance_date: Optional[datetime]
    next_maintenance_date: Optional[datetime]
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def display_name(self) -> str:
        return f"{self.unit_code}"
    
    @computed_field
    @property
    def is_available(self) -> bool:
        return self.status == InventoryUnitStatus.AVAILABLE and self.is_active
    
    @computed_field
    @property
    def is_rented(self) -> bool:
        return self.status == InventoryUnitStatus.RENTED
    
    @computed_field
    @property
    def is_sold(self) -> bool:
        return self.status == InventoryUnitStatus.SOLD


class InventoryUnitListResponse(BaseModel):
    """Schema for inventory unit list response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    item_id: UUID
    location_id: UUID
    unit_code: str
    serial_number: Optional[str]
    status: InventoryUnitStatus
    condition: InventoryUnitCondition
    purchase_price: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def display_name(self) -> str:
        return f"{self.unit_code}"


class InventoryUnitStatusUpdate(BaseModel):
    """Schema for updating inventory unit status."""
    status: InventoryUnitStatus = Field(..., description="New status")
    condition: Optional[InventoryUnitCondition] = Field(None, description="New condition")
    notes: Optional[str] = Field(None, description="Additional notes")


class StockLevelCreate(BaseModel):
    """Schema for creating a new stock level."""
    item_id: UUID = Field(..., description="Item ID")
    location_id: UUID = Field(..., description="Location ID")
    quantity_on_hand: str = Field(default="0", description="Current quantity on hand")
    quantity_available: str = Field(default="0", description="Available quantity")
    quantity_reserved: str = Field(default="0", description="Reserved quantity")
    quantity_on_order: str = Field(default="0", description="Quantity on order")
    minimum_level: str = Field(default="0", description="Minimum stock level")
    maximum_level: str = Field(default="0", description="Maximum stock level")
    reorder_point: str = Field(default="0", description="Reorder point")
    
    @field_validator('quantity_on_hand', 'quantity_available', 'quantity_reserved', 'quantity_on_order', 'minimum_level', 'maximum_level', 'reorder_point')
    @classmethod
    def validate_numeric_string(cls, v):
        if v is not None and v != "":
            try:
                quantity = int(v)
                if quantity < 0:
                    raise ValueError("Quantity cannot be negative")
            except ValueError:
                raise ValueError("Must be a valid number")
        return v


class StockLevelUpdate(BaseModel):
    """Schema for updating stock level."""
    quantity_on_hand: Optional[str] = Field(None, description="Current quantity on hand")
    quantity_available: Optional[str] = Field(None, description="Available quantity")
    quantity_reserved: Optional[str] = Field(None, description="Reserved quantity")
    quantity_on_order: Optional[str] = Field(None, description="Quantity on order")
    minimum_level: Optional[str] = Field(None, description="Minimum stock level")
    maximum_level: Optional[str] = Field(None, description="Maximum stock level")
    reorder_point: Optional[str] = Field(None, description="Reorder point")
    
    @field_validator('quantity_on_hand', 'quantity_available', 'quantity_reserved', 'quantity_on_order', 'minimum_level', 'maximum_level', 'reorder_point')
    @classmethod
    def validate_numeric_string(cls, v):
        if v is not None and v != "":
            try:
                quantity = int(v)
                if quantity < 0:
                    raise ValueError("Quantity cannot be negative")
            except ValueError:
                raise ValueError("Must be a valid number")
        return v


class StockLevelResponse(BaseModel):
    """Schema for stock level response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    item_id: UUID
    location_id: UUID
    quantity_on_hand: str
    quantity_available: str
    quantity_reserved: str
    quantity_on_order: str
    minimum_level: str
    maximum_level: str
    reorder_point: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def is_below_minimum(self) -> bool:
        return int(self.quantity_on_hand) < int(self.minimum_level)
    
    @computed_field
    @property
    def is_above_maximum(self) -> bool:
        return int(self.quantity_on_hand) > int(self.maximum_level)
    
    @computed_field
    @property
    def needs_reorder(self) -> bool:
        return int(self.quantity_on_hand) <= int(self.reorder_point)


class StockLevelListResponse(BaseModel):
    """Schema for stock level list response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    item_id: UUID
    location_id: UUID
    quantity_on_hand: str
    quantity_available: str
    quantity_reserved: str
    minimum_level: str
    maximum_level: str
    reorder_point: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def needs_reorder(self) -> bool:
        return int(self.quantity_on_hand) <= int(self.reorder_point)


class StockAdjustment(BaseModel):
    """Schema for stock adjustment."""
    adjustment: int = Field(..., description="Adjustment amount (positive or negative)")
    reason: Optional[str] = Field(None, description="Reason for adjustment")


class StockReservation(BaseModel):
    """Schema for stock reservation."""
    quantity: int = Field(..., ge=1, description="Quantity to reserve")
    reason: Optional[str] = Field(None, description="Reason for reservation")


class StockReservationRelease(BaseModel):
    """Schema for releasing stock reservation."""
    quantity: int = Field(..., ge=1, description="Quantity to release")
    reason: Optional[str] = Field(None, description="Reason for release")


class ItemWithInventoryResponse(BaseModel):
    """Schema for item with inventory details."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    item_code: str
    item_name: str
    item_type: ItemType
    item_status: ItemStatus
    purchase_price: Decimal
    rental_price_per_day: Optional[Decimal]
    sale_price: Optional[Decimal]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def display_name(self) -> str:
        return f"{self.item_name} ({self.item_code})"
    
    @computed_field
    @property
    def total_inventory_units(self) -> int:
        """This will be populated by the service layer."""
        return 0
    
    @computed_field
    @property
    def available_units(self) -> int:
        """This will be populated by the service layer."""
        return 0
    
    @computed_field
    @property
    def rented_units(self) -> int:
        """This will be populated by the service layer."""
        return 0


class InventoryReport(BaseModel):
    """Schema for inventory report."""
    items: List[ItemWithInventoryResponse]
    total_items: int
    total_active_items: int
    total_inventory_units: int
    total_available_units: int
    total_rented_units: int
    items_needing_reorder: List[ItemListResponse]
    
    
class InventoryUnitWithItemResponse(BaseModel):
    """Schema for inventory unit with item details."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    item_id: UUID
    location_id: UUID
    unit_code: str
    serial_number: Optional[str]
    status: InventoryUnitStatus
    condition: InventoryUnitCondition
    purchase_price: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def display_name(self) -> str:
        return f"{self.unit_code}"
    
    @computed_field
    @property
    def full_display_name(self) -> str:
        """This will be populated by the service layer with item info."""
        return f"{self.unit_code}"