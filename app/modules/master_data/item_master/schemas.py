from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator, computed_field, model_validator
from uuid import UUID

from app.modules.master_data.item_master.models import ItemStatus


class ItemCreate(BaseModel):
    """Schema for creating a new item."""
    model_config = ConfigDict(protected_namespaces=())
    
    item_name: str = Field(..., max_length=200, description="Item name")
    item_status: ItemStatus = Field(default=ItemStatus.ACTIVE, description="Item status")
    brand_id: Optional[UUID] = Field(None, description="Brand ID")
    category_id: Optional[UUID] = Field(None, description="Category ID")
    unit_of_measurement_id: UUID = Field(..., description="Unit of measurement ID")
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
    is_rentable: bool = Field(default=True, description="Item can be rented")
    is_saleable: bool = Field(default=False, description="Item can be sold")
    
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
    
    @field_validator('is_saleable')
    @classmethod
    def validate_boolean_exclusion(cls, v, info):
        """Validate that is_rentable and is_saleable are mutually exclusive."""
        is_rentable = info.data.get('is_rentable', True)  # Default value
        
        if v and is_rentable:
            raise ValueError("Item cannot be both rentable and saleable - these are mutually exclusive")
        
        if not v and not is_rentable:
            raise ValueError("Item must be either rentable or saleable")
        
        return v


class ItemUpdate(BaseModel):
    """Schema for updating an item."""
    model_config = ConfigDict(protected_namespaces=())
    
    item_name: Optional[str] = Field(None, max_length=200, description="Item name")
    item_status: Optional[ItemStatus] = Field(None, description="Item status")
    brand_id: Optional[UUID] = Field(None, description="Brand ID")
    category_id: Optional[UUID] = Field(None, description="Category ID")
    unit_of_measurement_id: Optional[UUID] = Field(None, description="Unit of measurement ID")
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
    is_rentable: Optional[bool] = Field(None, description="Item can be rented")
    is_saleable: Optional[bool] = Field(None, description="Item can be sold")
    
    @field_validator('minimum_rental_days', 'maximum_rental_days', 'warranty_period_days', 'reorder_level', 'reorder_quantity')
    @classmethod
    def validate_numeric_string(cls, v):
        if v is not None and v != "":
            try:
                int(v)
            except ValueError:
                raise ValueError("Must be a valid number")
        return v
    
    @model_validator(mode='after')
    def validate_boolean_fields(self):
        """Validate boolean field combinations for updates."""
        if self.is_rentable is not None and self.is_saleable is not None:
            if self.is_rentable and self.is_saleable:
                raise ValueError("Item cannot be both rentable and saleable - these are mutually exclusive")
            if not self.is_rentable and not self.is_saleable:
                raise ValueError("Item must be either rentable or saleable")
        return self


class ItemResponse(BaseModel):
    """Schema for item response."""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    
    id: UUID
    sku: str
    item_name: str
    item_status: ItemStatus
    brand_id: Optional[UUID]
    category_id: Optional[UUID]
    unit_of_measurement_id: UUID
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
    is_rentable: bool
    is_saleable: bool
    is_active: Optional[bool] = True
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def display_name(self) -> str:
        return f"{self.item_name} ({self.sku})"
    
    @computed_field
    @property
    def is_rental_item(self) -> bool:
        return self.is_rentable
    
    @computed_field
    @property
    def is_sale_item(self) -> bool:
        return self.is_saleable


class ItemListResponse(BaseModel):
    """Schema for item list response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    sku: str
    item_name: str
    item_status: ItemStatus
    rental_price_per_day: Optional[Decimal]
    sale_price: Optional[Decimal]
    is_rentable: bool
    is_saleable: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def display_name(self) -> str:
        return f"{self.item_name} ({self.sku})"


class ItemWithInventoryResponse(BaseModel):
    """Schema for item response with inventory details."""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    
    id: UUID
    sku: str
    item_name: str
    item_status: ItemStatus
    brand_id: Optional[UUID]
    category_id: Optional[UUID]
    unit_of_measurement_id: UUID
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
    is_rentable: bool
    is_saleable: bool
    is_active: Optional[bool] = True
    created_at: datetime
    updated_at: datetime
    
    # Inventory summary fields
    total_inventory_units: int = Field(default=0, description="Total number of inventory units")
    available_units: int = Field(default=0, description="Number of available units")
    rented_units: int = Field(default=0, description="Number of rented units")
    
    @computed_field
    @property
    def display_name(self) -> str:
        return f"{self.item_name} ({self.sku})"
    
    @computed_field
    @property
    def is_rental_item(self) -> bool:
        return self.is_rentable
    
    @computed_field
    @property
    def is_sale_item(self) -> bool:
        return self.is_saleable


# SKU-specific schemas
class SKUGenerationRequest(BaseModel):
    """Schema for SKU generation request."""
    
    category_id: Optional[UUID] = Field(None, description="Category ID for SKU generation")
    item_name: str = Field(..., description="Item name for product code generation")
    is_rentable: bool = Field(default=True, description="Item can be rented")
    is_saleable: bool = Field(default=False, description="Item can be sold")


class SKUGenerationResponse(BaseModel):
    """Schema for SKU generation response."""
    
    sku: str = Field(..., description="Generated SKU")
    category_code: str = Field(..., description="Category code used")
    subcategory_code: str = Field(..., description="Subcategory code used")
    product_code: str = Field(..., description="Product code (first 4 letters of item name)")
    attributes_code: str = Field(..., description="Attributes code (R/S/B)")
    sequence_number: int = Field(..., description="Sequence number used")


class SKUBulkGenerationResponse(BaseModel):
    """Schema for bulk SKU generation response."""
    
    total_processed: int = Field(..., description="Total items processed")
    successful_generations: int = Field(..., description="Number of successful generations")
    failed_generations: int = Field(..., description="Number of failed generations")
    errors: List[dict] = Field(default_factory=list, description="Generation errors")