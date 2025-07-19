"""
Rentals Schemas

Pydantic schemas for rental-related operations.
"""

from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from uuid import UUID

from app.modules.transactions.models import TransactionType, TransactionStatus, PaymentStatus, RentalStatus, RentalPeriodUnit


# Nested response schemas for rental details
class CustomerNestedResponse(BaseModel):
    """Schema for nested customer response in rental transactions."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str = Field(..., description="Customer name")


class LocationNestedResponse(BaseModel):
    """Schema for nested location response in rental transactions."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str = Field(..., description="Location name")


class ItemNestedResponse(BaseModel):
    """Schema for nested item response in rental transactions."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str = Field(..., description="Item name")


class BrandNested(BaseModel):
    """Nested brand information for rentable items."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


class CategoryNested(BaseModel):
    """Nested category information for rentable items."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


class UnitOfMeasurementNested(BaseModel):
    """Nested unit of measurement information."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    abbreviation: str


class LocationAvailability(BaseModel):
    """Location-wise availability information for rentable items."""

    model_config = ConfigDict(from_attributes=True)

    location_id: UUID = Field(..., description="Location ID")
    location_name: str = Field(..., description="Location name")
    available_quantity: float = Field(..., description="Available quantity at this location")


class RentalItemCreate(BaseModel):
    """Schema for creating a rental item."""
    
    item_id: str = Field(..., description="Item ID")
    quantity: int = Field(..., ge=0, description="Quantity")
    rental_period_value: int = Field(..., ge=0, description="Rental period value")
    tax_rate: Optional[Decimal] = Field(0, ge=0, le=100, description="Tax rate percentage")
    discount_amount: Optional[Decimal] = Field(0, ge=0, description="Discount amount")
    rental_start_date: str = Field(..., description="Rental start date in YYYY-MM-DD format")
    rental_end_date: str = Field(..., description="Rental end date in YYYY-MM-DD format")
    notes: Optional[str] = Field("", description="Additional notes")
    
    @field_validator("rental_start_date", "rental_end_date")
    @classmethod
    def validate_rental_dates(cls, v):
        """Validate and parse rental dates."""
        try:
            from datetime import datetime
            return datetime.strptime(v, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD format.")
    
    @model_validator(mode="after")
    def validate_rental_date_range(self):
        """Validate rental end date is after start date."""
        if self.rental_end_date <= self.rental_start_date:
            raise ValueError("Rental end date must be after start date")
        return self


class RentalLineItemResponse(BaseModel):
    """Schema for rental line item response with rental-specific fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    item: ItemNestedResponse = Field(..., description="Item details")
    quantity: Decimal
    unit_price: Decimal = Field(..., description="Rental rate per period")
    tax_rate: Decimal = Field(..., description="Tax rate percentage")
    discount_amount: Decimal = Field(..., description="Discount amount")
    rental_period_value: int = Field(..., description="Rental period value")
    rental_period_unit: RentalPeriodUnit = Field(..., description="Rental period unit")
    rental_start_date: date = Field(..., description="Rental start date")
    rental_end_date: date = Field(..., description="Rental end date")
    current_rental_status: Optional[RentalStatus] = Field(None, description="Current rental status")
    notes: str = Field(default="", description="Additional notes")
    tax_amount: Decimal = Field(..., description="Calculated tax amount")
    line_total: Decimal = Field(..., description="Total line amount")
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_transaction_line(cls, line: dict, item_details: dict = None) -> "RentalLineItemResponse":
        """Create RentalLineItemResponse from TransactionLine data."""
        # Create item nested response
        item_nested = ItemNestedResponse(
            id=item_details["id"] if item_details else line["item_id"],
            name=item_details["name"] if item_details else "Unknown Item"
        )
        
        return cls(
            id=line["id"],
            item=item_nested,
            quantity=line["quantity"],
            unit_price=line["unit_price"],
            tax_rate=line["tax_rate"],
            discount_amount=line["discount_amount"],
            rental_period_value=line.get("rental_period", line.get("rental_period_value", 1)),
            rental_period_unit=line.get("rental_period_unit", RentalPeriodUnit.DAYS),
            rental_start_date=line["rental_start_date"],
            rental_end_date=line["rental_end_date"],
            current_rental_status=line.get("current_rental_status"),
            notes=line.get("notes", ""),
            tax_amount=line["tax_amount"],
            line_total=line["line_total"],
            created_at=line["created_at"],
            updated_at=line["updated_at"],
        )


class NewRentalRequest(BaseModel):
    """Schema for the new-rental endpoint - matches frontend JSON structure exactly."""
    
    transaction_date: str = Field(..., description="Transaction date in YYYY-MM-DD format")
    customer_id: str = Field(..., description="Customer ID")
    location_id: str = Field(..., description="Location ID")
    payment_method: str = Field(..., description="Payment method")
    payment_reference: Optional[str] = Field("", description="Payment reference")
    notes: Optional[str] = Field("", description="Additional notes")
    items: List[RentalItemCreate] = Field(..., min_length=1, description="Rental items")
    
    # New delivery fields
    delivery_required: bool = Field(False, description="Whether delivery is required")
    delivery_address: Optional[str] = Field(None, description="Delivery address")
    delivery_date: Optional[str] = Field(None, description="Delivery date in YYYY-MM-DD format")
    delivery_time: Optional[str] = Field(None, description="Delivery time in HH:MM format")
    
    # New pickup fields
    pickup_required: bool = Field(False, description="Whether pickup is required")
    pickup_date: Optional[str] = Field(None, description="Pickup date in YYYY-MM-DD format")
    pickup_time: Optional[str] = Field(None, description="Pickup time in HH:MM format")
    
    # Deposit amount (add reference_number alias for transaction_number)
    deposit_amount: Optional[Decimal] = Field(None, ge=0, description="Security deposit amount")
    reference_number: Optional[str] = Field(None, description="Reference number for the rental")
    
    @field_validator("transaction_date")
    @classmethod
    def validate_transaction_date(cls, v):
        """Validate and parse transaction date."""
        try:
            from datetime import datetime
            return datetime.strptime(v, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD format.")
    
    @field_validator("customer_id", "location_id")
    @classmethod
    def validate_uuids(cls, v):
        """Validate UUID strings."""
        try:
            from uuid import UUID
            return UUID(v)
        except ValueError:
            raise ValueError(f"Invalid UUID format: {v}")
    
    @field_validator("delivery_date", "pickup_date")
    @classmethod
    def validate_optional_dates(cls, v):
        """Validate optional date fields."""
        if v is None:
            return None
        try:
            from datetime import datetime
            return datetime.strptime(v, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD format.")
    
    @field_validator("delivery_time", "pickup_time")
    @classmethod
    def validate_optional_times(cls, v):
        """Validate optional time fields."""
        if v is None:
            return None
        try:
            from datetime import datetime
            datetime.strptime(v, "%H:%M")
            return v
        except ValueError:
            raise ValueError("Invalid time format. Use HH:MM format.")
    
    @model_validator(mode="after")
    def validate_delivery_fields(self):
        """Validate delivery fields consistency."""
        if self.delivery_required:
            if not self.delivery_address:
                raise ValueError("Delivery address is required when delivery is required")
            if not self.delivery_date:
                raise ValueError("Delivery date is required when delivery is required")
        return self
    
    @model_validator(mode="after")
    def validate_pickup_fields(self):
        """Validate pickup fields consistency."""
        if self.pickup_required:
            if not self.pickup_date:
                raise ValueError("Pickup date is required when pickup is required")
        return self


class NewRentalResponse(BaseModel):
    """Schema for new-rental response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    success: bool = Field(True, description="Operation success status")
    message: str = Field("Rental created successfully", description="Response message")
    data: dict = Field(..., description="Rental transaction data")
    transaction_id: UUID = Field(..., description="Created transaction ID")
    transaction_number: str = Field(..., description="Generated transaction number")


class RentalResponse(BaseModel):
    """Schema for rental response - maps transaction data to rental format."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer: CustomerNestedResponse = Field(..., description="Customer details")
    location: LocationNestedResponse = Field(..., description="Location details")
    transaction_date: date = Field(..., description="Transaction date")
    reference_number: Optional[str] = Field(None, description="Reference number")
    notes: Optional[str] = Field(None, description="Additional notes")
    subtotal: Decimal = Field(..., description="Subtotal amount")
    tax_amount: Decimal = Field(..., description="Tax amount")
    discount_amount: Decimal = Field(..., description="Discount amount")
    total_amount: Decimal = Field(..., description="Total amount")
    deposit_amount: Decimal = Field(..., description="Security deposit amount")
    status: str = Field(..., description="Rental status")
    payment_status: str = Field(..., description="Payment status")
    delivery_required: bool = Field(False, description="Whether delivery is required")
    delivery_address: Optional[str] = Field(None, description="Delivery address")
    delivery_date: Optional[date] = Field(None, description="Delivery date")
    delivery_time: Optional[str] = Field(None, description="Delivery time")
    pickup_required: bool = Field(False, description="Whether pickup is required")
    pickup_date: Optional[date] = Field(None, description="Pickup date")
    pickup_time: Optional[str] = Field(None, description="Pickup time")
    created_at: datetime
    updated_at: datetime
    items: List[RentalLineItemResponse] = Field(default_factory=list, description="Rental items")

    @classmethod
    def from_transaction(cls, transaction: dict, customer_details: dict = None, location_details: dict = None, items_details: dict = None) -> "RentalResponse":
        """Create RentalResponse from TransactionHeaderResponse data."""
        # Create nested customer response
        customer_nested = CustomerNestedResponse(
            id=customer_details["id"] if customer_details else transaction["customer_id"],
            name=customer_details["name"] if customer_details else "Unknown Customer"
        )
        
        # Create nested location response
        location_nested = LocationNestedResponse(
            id=location_details["id"] if location_details else transaction["location_id"],
            name=location_details["name"] if location_details else "Unknown Location"
        )
        
        # Transform transaction lines to rental line items
        rental_items = []
        items_details = items_details or {}
        for line in transaction.get("transaction_lines", []):
            item_detail = items_details.get(str(line["item_id"]), None)
            rental_items.append(RentalLineItemResponse.from_transaction_line(line, item_detail))
        
        return cls(
            id=transaction["id"],
            customer=customer_nested,
            location=location_nested,
            transaction_date=transaction["transaction_date"].date()
            if isinstance(transaction["transaction_date"], datetime)
            else transaction["transaction_date"],
            reference_number=transaction.get("transaction_number"),
            notes=transaction.get("notes"),
            subtotal=transaction["subtotal"],
            tax_amount=transaction["tax_amount"],
            discount_amount=transaction["discount_amount"],
            total_amount=transaction["total_amount"],
            deposit_amount=transaction.get("deposit_amount", Decimal("0")),
            status=transaction["status"],
            payment_status=transaction["payment_status"],
            delivery_required=transaction.get("delivery_required", False),
            delivery_address=transaction.get("delivery_address"),
            delivery_date=transaction.get("delivery_date"),
            delivery_time=transaction.get("delivery_time"),
            pickup_required=transaction.get("pickup_required", False),
            pickup_date=transaction.get("pickup_date"),
            pickup_time=transaction.get("pickup_time"),
            created_at=transaction["created_at"],
            updated_at=transaction["updated_at"],
            items=rental_items,
        )


class RentalPeriodUpdate(BaseModel):
    """Schema for updating rental period."""

    new_end_date: date = Field(..., description="New rental end date")
    reason: Optional[str] = Field(None, description="Reason for change")
    notes: Optional[str] = Field(None, description="Additional notes")


class RentalReturn(BaseModel):
    """Schema for rental return."""

    actual_return_date: date = Field(..., description="Actual return date")
    condition_notes: Optional[str] = Field(None, description="Condition notes")
    late_fees: Optional[Decimal] = Field(None, ge=0, description="Late fees")
    damage_fees: Optional[Decimal] = Field(None, ge=0, description="Damage fees")
    notes: Optional[str] = Field(None, description="Additional notes")


class RentableItemResponse(BaseModel):
    """Rentable item with stock position across locations."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Item ID")
    sku: str = Field(..., description="Stock Keeping Unit")
    item_name: str = Field(..., description="Item name")
    rental_rate_per_period: Decimal = Field(..., description="Rental rate per period")
    rental_period: str = Field(..., description="Rental period (number of periods)")
    security_deposit: Decimal = Field(..., description="Security deposit amount")
    total_available_quantity: float = Field(..., description="Total available quantity across all locations")
    brand: Optional[BrandNested] = Field(None, description="Brand information")
    category: Optional[CategoryNested] = Field(None, description="Category information")
    unit_of_measurement: UnitOfMeasurementNested = Field(..., description="Unit of measurement")
    location_availability: List[LocationAvailability] = Field(..., description="Availability breakdown by location")


class RentalDetail(BaseModel):
    """Schema for detailed rental information."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    transaction_number: str
    customer_id: UUID
    customer_name: Optional[str] = None
    location_id: UUID
    location_name: Optional[str] = None
    transaction_date: date
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    deposit_amount: Decimal
    paid_amount: Decimal
    status: TransactionStatus
    payment_status: PaymentStatus
    delivery_required: bool
    delivery_address: Optional[str] = None
    delivery_date: Optional[date] = None
    delivery_time: Optional[str] = None
    pickup_required: bool
    pickup_date: Optional[date] = None
    pickup_time: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[RentalLineItemResponse] = Field(default_factory=list)


class RentalListResponse(BaseModel):
    """Response schema for rental list."""
    
    rentals: List[RentalResponse] = Field(default_factory=list)
    total: int
    page: int
    page_size: int
    total_pages: int