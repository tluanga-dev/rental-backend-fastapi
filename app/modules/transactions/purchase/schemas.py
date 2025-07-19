"""
Purchase Schemas

Pydantic schemas for purchase-related operations.
"""

from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator
from uuid import UUID

from app.modules.transactions.models import TransactionType, TransactionStatus, PaymentStatus


# Nested response schemas for purchase details
class SupplierNestedResponse(BaseModel):
    """Schema for nested supplier response in purchase transactions."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str = Field(..., description="Supplier name")


class LocationNestedResponse(BaseModel):
    """Schema for nested location response in purchase transactions."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str = Field(..., description="Location name")


class ItemNestedResponse(BaseModel):
    """Schema for nested item response in purchase transactions."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str = Field(..., description="Item name")


class PurchaseItemCreate(BaseModel):
    """Schema for creating a purchase item."""

    item_id: str = Field(..., description="Item ID")
    quantity: int = Field(..., ge=1, description="Quantity")
    unit_cost: Decimal = Field(..., ge=0, description="Unit cost")
    tax_rate: Optional[Decimal] = Field(0, ge=0, le=100, description="Tax rate percentage")
    discount_amount: Optional[Decimal] = Field(0, ge=0, description="Discount amount")
    condition: str = Field(..., pattern="^[A-D]$", description="Item condition (A, B, C, or D)")
    notes: Optional[str] = Field("", description="Additional notes")


class PurchaseLineItemResponse(BaseModel):
    """Schema for purchase line item response with purchase-specific fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    item: ItemNestedResponse = Field(..., description="Item details")
    quantity: Decimal
    unit_cost: Decimal = Field(..., description="Unit cost per item")
    tax_rate: Decimal = Field(..., description="Tax rate percentage")
    discount_amount: Decimal = Field(..., description="Discount amount")
    condition: str = Field(..., description="Item condition (A, B, C, or D)")
    notes: str = Field(default="", description="Additional notes")
    tax_amount: Decimal = Field(..., description="Calculated tax amount")
    line_total: Decimal = Field(..., description="Total line amount")
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_transaction_line(cls, line: dict, item_details: dict = None) -> "PurchaseLineItemResponse":
        """Create PurchaseLineItemResponse from TransactionLine data."""
        # Extract condition from description if available
        condition = "A"  # Default condition
        description = line.get("description", "")
        if "(Condition: " in description and ")" in description:
            condition_start = description.find("(Condition: ") + len("(Condition: ")
            condition_end = description.find(")", condition_start)
            condition = description[condition_start:condition_end].strip()
        
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
            condition=condition,
            notes=line.get("notes", ""),
            tax_amount=line["tax_amount"],
            line_total=line["line_total"],
            created_at=line["created_at"],
            updated_at=line["updated_at"],
        )


class PurchaseCreate(BaseModel):
    """Schema for creating a purchase transaction."""

    supplier_id: UUID = Field(..., description="Supplier ID")
    location_id: UUID = Field(..., description="Location ID")
    purchase_date: date = Field(..., description="Purchase date")
    notes: Optional[str] = Field("", description="Additional notes")
    reference_number: Optional[str] = Field("", max_length=50, description="Reference number")
    items: List[PurchaseItemCreate] = Field(..., min_length=1, description="Purchase items")


class PurchaseLineRequest(BaseModel):
    """Schema for purchase line item request."""
    
    item_id: UUID = Field(..., description="Item ID")
    quantity: Decimal = Field(..., gt=0, description="Quantity")
    unit_cost: Decimal = Field(..., ge=0, description="Unit cost")
    tax_rate: Optional[Decimal] = Field(0, ge=0, le=100, description="Tax rate percentage")
    discount_amount: Optional[Decimal] = Field(0, ge=0, description="Discount amount")
    condition: str = Field("A", pattern="^[A-D]$", description="Item condition (A, B, C, or D)")
    notes: Optional[str] = Field("", description="Additional notes")


class NewPurchaseRequest(BaseModel):
    """Schema for the new-purchase endpoint - matches frontend JSON structure exactly."""

    supplier_id: str = Field(..., description="Supplier ID")
    location_id: str = Field(..., description="Location ID")
    purchase_date: str = Field(..., description="Purchase date in YYYY-MM-DD format")
    notes: str = Field("", description="Additional notes")
    reference_number: str = Field("", description="Reference number")
    items: List[PurchaseItemCreate] = Field(..., min_length=1, description="Purchase items")

    @field_validator("purchase_date")
    @classmethod
    def validate_purchase_date(cls, v):
        """Validate and parse the purchase date."""
        try:
            from datetime import datetime

            return datetime.strptime(v, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD format.")

    @field_validator("supplier_id", "location_id")
    @classmethod
    def validate_uuids(cls, v):
        """Validate UUID strings."""
        try:
            from uuid import UUID

            return UUID(v)
        except ValueError:
            raise ValueError(f"Invalid UUID format: {v}")


class NewPurchaseResponse(BaseModel):
    """Schema for new-purchase response."""

    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(True, description="Operation success status")
    message: str = Field("Purchase created successfully", description="Response message")
    data: dict = Field(..., description="Purchase transaction data")
    transaction_id: UUID = Field(..., description="Created transaction ID")
    transaction_number: str = Field(..., description="Generated transaction number")


class PurchaseResponse(BaseModel):
    """Schema for purchase response - maps transaction data to purchase format."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    supplier: SupplierNestedResponse = Field(..., description="Supplier details")
    location: LocationNestedResponse = Field(..., description="Location details")
    purchase_date: date = Field(..., description="Purchase date (mapped from transaction_date)")
    reference_number: Optional[str] = Field(
        None, description="Reference number (mapped from transaction_number)"
    )
    notes: Optional[str] = Field(None, description="Additional notes")
    subtotal: Decimal = Field(..., description="Subtotal amount")
    tax_amount: Decimal = Field(..., description="Tax amount")
    discount_amount: Decimal = Field(..., description="Discount amount")
    total_amount: Decimal = Field(..., description="Total amount")
    status: str = Field(..., description="Purchase status")
    payment_status: str = Field(..., description="Payment status")
    created_at: datetime
    updated_at: datetime
    items: List[PurchaseLineItemResponse] = Field(default_factory=list, description="Purchase items")

    @classmethod
    def from_transaction(cls, transaction: dict, supplier_details: dict = None, location_details: dict = None, items_details: dict = None) -> "PurchaseResponse":
        """Create PurchaseResponse from TransactionHeaderResponse data."""
        # Create nested supplier response
        supplier_nested = SupplierNestedResponse(
            id=supplier_details["id"] if supplier_details else transaction["customer_id"],
            name=supplier_details["name"] if supplier_details else "Unknown Supplier"
        )
        
        # Create nested location response
        location_nested = LocationNestedResponse(
            id=location_details["id"] if location_details else transaction["location_id"],
            name=location_details["name"] if location_details else "Unknown Location"
        )
        
        # Transform transaction lines to purchase line items
        purchase_items = []
        items_details = items_details or {}
        for line in transaction.get("transaction_lines", []):
            item_detail = items_details.get(str(line["item_id"]), None)
            purchase_items.append(PurchaseLineItemResponse.from_transaction_line(line, item_detail))
        
        return cls(
            id=transaction["id"],
            supplier=supplier_nested,
            location=location_nested,
            purchase_date=transaction["transaction_date"].date()
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
            items=purchase_items,
        )


class PurchaseDetail(BaseModel):
    """Schema for detailed purchase information."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    transaction_number: str
    supplier_id: UUID
    supplier_name: Optional[str] = None
    location_id: UUID
    location_name: Optional[str] = None
    purchase_date: date
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
    items: List[PurchaseLineItemResponse] = Field(default_factory=list)


class PurchaseListResponse(BaseModel):
    """Response schema for purchase list."""
    
    purchases: List[PurchaseResponse] = Field(default_factory=list)
    total: int
    page: int
    page_size: int
    total_pages: int