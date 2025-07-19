"""
Sales Schemas

Pydantic schemas for sales-related operations.
"""

from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator
from uuid import UUID

from app.modules.transactions.models import TransactionType, TransactionStatus, PaymentStatus


# Nested response schemas for sales details
class CustomerNestedResponse(BaseModel):
    """Schema for nested customer response in sale transactions."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str = Field(..., description="Customer name")


class LocationNestedResponse(BaseModel):
    """Schema for nested location response in sale transactions."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str = Field(..., description="Location name")


class ItemNestedResponse(BaseModel):
    """Schema for nested item response in sale transactions."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str = Field(..., description="Item name")


class SaleItemCreate(BaseModel):
    """Schema for creating a sale item."""

    item_id: str = Field(..., description="Item ID")
    quantity: int = Field(..., ge=1, description="Quantity")
    unit_cost: Decimal = Field(..., ge=0, description="Unit cost")
    tax_rate: Optional[Decimal] = Field(0, ge=0, le=100, description="Tax rate percentage")
    discount_amount: Optional[Decimal] = Field(0, ge=0, description="Discount amount")
    notes: Optional[str] = Field("", description="Additional notes")

    @field_validator("item_id")
    @classmethod
    def validate_item_id(cls, v):
        """Validate item ID as UUID."""
        try:
            from uuid import UUID
            return UUID(v)
        except ValueError:
            raise ValueError(f"Invalid UUID format: {v}")


class SaleLineItemResponse(BaseModel):
    """Schema for sale line item response with sale-specific fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    item: ItemNestedResponse = Field(..., description="Item details")
    quantity: Decimal
    unit_cost: Decimal = Field(..., description="Unit cost per item")
    tax_rate: Decimal = Field(..., description="Tax rate percentage")
    discount_amount: Decimal = Field(..., description="Discount amount")
    notes: str = Field(default="", description="Additional notes")
    tax_amount: Decimal = Field(..., description="Calculated tax amount")
    line_total: Decimal = Field(..., description="Total line amount")
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_transaction_line(cls, line: dict, item_details: dict = None) -> "SaleLineItemResponse":
        """Create SaleLineItemResponse from TransactionLine data."""
        # Create item nested response
        item_nested = ItemNestedResponse(
            id=item_details["id"] if item_details else line["item_id"],
            name=item_details["name"] if item_details else "Unknown Item"
        )
        
        return cls(
            id=line["id"],
            item=item_nested,
            quantity=line["quantity"],
            unit_cost=line["unit_price"],  # Map unit_price to unit_cost
            tax_rate=line["tax_rate"],
            discount_amount=line["discount_amount"],
            notes=line.get("notes", ""),
            tax_amount=line["tax_amount"],
            line_total=line["line_total"],
            created_at=line["created_at"],
            updated_at=line["updated_at"],
        )


class SaleCreate(BaseModel):
    """Schema for creating a sale transaction."""

    customer_id: UUID = Field(..., description="Customer ID")
    location_id: UUID = Field(..., description="Location ID")
    transaction_date: date = Field(..., description="Sale date")
    notes: Optional[str] = Field("", description="Additional notes")
    reference_number: Optional[str] = Field("", max_length=50, description="Reference number")
    items: List[SaleItemCreate] = Field(..., min_length=1, description="Sale items")


class NewSaleRequest(BaseModel):
    """Schema for the new-sale endpoint - matches frontend JSON structure exactly."""

    customer_id: str = Field(..., description="Customer ID")
    transaction_date: str = Field(..., description="Transaction date in YYYY-MM-DD format")
    notes: Optional[str] = Field("", description="Additional notes")
    reference_number: Optional[str] = Field("", max_length=50, description="Reference number")
    items: List[SaleItemCreate] = Field(..., min_length=1, description="Sale items")

    @field_validator("transaction_date")
    @classmethod
    def validate_transaction_date(cls, v):
        """Validate and parse transaction date."""
        try:
            from datetime import datetime
            return datetime.strptime(v, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD format.")

    @field_validator("customer_id")
    @classmethod
    def validate_customer_id(cls, v):
        """Validate customer ID as UUID."""
        try:
            from uuid import UUID
            return UUID(v)
        except ValueError:
            raise ValueError(f"Invalid UUID format: {v}")


class NewSaleResponse(BaseModel):
    """Schema for new-sale response."""

    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(True, description="Operation success status")
    message: str = Field("Sale created successfully", description="Response message")
    data: dict = Field(..., description="Sale transaction data")
    transaction_id: UUID = Field(..., description="Created transaction ID")
    transaction_number: str = Field(..., description="Generated transaction number")


class SaleResponse(BaseModel):
    """Schema for sale response - maps transaction data to sale format."""

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
    status: str = Field(..., description="Sale status")
    payment_status: str = Field(..., description="Payment status")
    created_at: datetime
    updated_at: datetime
    items: List[SaleLineItemResponse] = Field(default_factory=list, description="Sale items")

    @classmethod
    def from_transaction(cls, transaction: dict, customer_details: dict = None, location_details: dict = None, items_details: dict = None) -> "SaleResponse":
        """Create SaleResponse from TransactionHeaderResponse data."""
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
        
        # Transform transaction lines to sale line items
        sale_items = []
        items_details = items_details or {}
        for line in transaction.get("transaction_lines", []):
            item_detail = items_details.get(str(line["item_id"]), None)
            sale_items.append(SaleLineItemResponse.from_transaction_line(line, item_detail))
        
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
            status=transaction["status"],
            payment_status=transaction["payment_status"],
            created_at=transaction["created_at"],
            updated_at=transaction["updated_at"],
            items=sale_items,
        )


class SaleDetail(BaseModel):
    """Schema for detailed sale information."""
    
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
    paid_amount: Decimal
    status: TransactionStatus
    payment_status: PaymentStatus
    created_at: datetime
    updated_at: datetime
    items: List[SaleLineItemResponse] = Field(default_factory=list)


class SaleListResponse(BaseModel):
    """Response schema for sale list."""
    
    sales: List[SaleResponse] = Field(default_factory=list)
    total: int
    page: int
    page_size: int
    total_pages: int