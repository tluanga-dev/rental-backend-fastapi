from typing import Optional, List, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator, computed_field
from uuid import UUID

from app.modules.master_data.item_master.models import ItemStatus
from app.modules.inventory.models import InventoryUnitStatus, InventoryUnitCondition, MovementType, ReferenceType
# Simplified approach - using string with pattern validation



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
    quantity_on_hand: Decimal = Field(default=Decimal("0"), ge=0, description="Current quantity on hand")
    quantity_available: Decimal = Field(default=Decimal("0"), ge=0, description="Available quantity")
    quantity_on_rent: Decimal = Field(default=Decimal("0"), ge=0, description="Quantity currently on rent")


class StockLevelUpdate(BaseModel):
    """Schema for updating stock level."""
    quantity_on_hand: Optional[Decimal] = Field(None, ge=0, description="Current quantity on hand")
    quantity_available: Optional[Decimal] = Field(None, ge=0, description="Available quantity")
    quantity_on_rent: Optional[Decimal] = Field(None, ge=0, description="Quantity currently on rent")


class StockLevelResponse(BaseModel):
    """Schema for stock level response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    item_id: UUID
    location_id: UUID
    quantity_on_hand: Decimal
    quantity_available: Decimal
    quantity_on_rent: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def total_allocated(self) -> Decimal:
        """Total quantity allocated (available + on rent)."""
        return self.quantity_available + self.quantity_on_rent
    
    @computed_field
    @property
    def is_available_for_rent(self) -> bool:
        """Check if any quantity is available for rent."""
        return self.quantity_available > 0 and self.is_active


class StockLevelListResponse(BaseModel):
    """Schema for stock level list response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    item_id: UUID
    location_id: UUID
    quantity_on_hand: Decimal
    quantity_available: Decimal
    quantity_on_rent: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime


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


class InventoryReport(BaseModel):
    """Schema for inventory report."""
    
    items: List[Any]  # Will be ItemWithInventoryResponse from item_master
    total_items: int
    total_active_items: int
    total_inventory_units: int
    total_available_units: int
    total_rented_units: int
    items_needing_reorder: List[Any]  # Will be ItemListResponse from item_master
    
    
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


# Stock Movement Schemas

class StockMovementCreate(BaseModel):
    """Schema for creating a stock movement record."""
    stock_level_id: UUID = Field(..., description="Stock level ID")
    movement_type: MovementType = Field(..., description="Type of movement")
    reference_type: ReferenceType = Field(..., description="Type of reference")
    reference_id: str = Field(..., max_length=100, description="External reference ID")
    quantity_change: Decimal = Field(..., description="Quantity change (+/-)")
    quantity_before: Decimal = Field(..., ge=0, description="Quantity before movement")
    quantity_after: Decimal = Field(..., ge=0, description="Quantity after movement")
    reason: str = Field(..., max_length=500, description="Reason for movement")
    notes: Optional[str] = Field(None, description="Additional notes")
    transaction_line_id: Optional[UUID] = Field(None, description="Transaction line reference")


class StockMovementResponse(BaseModel):
    """Schema for stock movement response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    stock_level_id: UUID
    item_id: UUID
    location_id: UUID
    movement_type: MovementType
    reference_type: ReferenceType
    reference_id: Optional[str]
    quantity_change: Decimal
    quantity_before: Decimal
    quantity_after: Decimal
    reason: str
    notes: Optional[str]
    transaction_line_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID]
    is_active: bool
    
    @computed_field
    @property
    def is_increase(self) -> bool:
        """Check if this movement increases stock."""
        return self.quantity_change > 0
    
    @computed_field
    @property
    def is_decrease(self) -> bool:
        """Check if this movement decreases stock."""
        return self.quantity_change < 0
    
    @computed_field
    @property
    def display_name(self) -> str:
        """Get movement display name."""
        direction = "+" if self.quantity_change >= 0 else ""
        return f"{self.movement_type.value}: {direction}{self.quantity_change}"


class StockMovementListResponse(BaseModel):
    """Schema for stock movement list response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    movement_type: MovementType
    reference_type: ReferenceType
    reference_id: Optional[str]
    quantity_change: Decimal
    reason: str
    created_at: datetime
    created_by: Optional[UUID]


class StockMovementHistoryRequest(BaseModel):
    """Schema for requesting stock movement history."""
    stock_level_id: Optional[UUID] = Field(None, description="Filter by stock level ID")
    item_id: Optional[UUID] = Field(None, description="Filter by item ID")
    location_id: Optional[UUID] = Field(None, description="Filter by location ID")
    movement_type: Optional[MovementType] = Field(None, description="Filter by movement type")
    reference_type: Optional[ReferenceType] = Field(None, description="Filter by reference type")
    start_date: Optional[datetime] = Field(None, description="Start date for filtering")
    end_date: Optional[datetime] = Field(None, description="End date for filtering")
    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(default=100, ge=1, le=1000, description="Number of records to return")


class StockMovementSummaryResponse(BaseModel):
    """Schema for stock movement summary response."""
    total_movements: int
    total_increases: Decimal
    total_decreases: Decimal
    net_change: Decimal
    movement_types: dict = Field(default_factory=dict)
    
    
class StockMovementReportRequest(BaseModel):
    """Schema for stock movement report request."""
    item_id: Optional[UUID] = Field(None, description="Filter by item ID")
    location_id: Optional[UUID] = Field(None, description="Filter by location ID")
    start_date: Optional[datetime] = Field(None, description="Start date for report")
    end_date: Optional[datetime] = Field(None, description="End date for report")
    movement_type: Optional[MovementType] = Field(None, description="Filter by movement type")
    include_summary: bool = Field(default=True, description="Include summary statistics")
    include_details: bool = Field(default=False, description="Include detailed movements")


