"""
Purchase transaction schemas for validation and response formatting.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict


class ItemCondition(str, Enum):
    """Item condition enumeration."""
    A = "A"  # New/Excellent condition
    B = "B"  # Good condition
    C = "C"  # Fair condition
    D = "D"  # Poor condition


class PurchaseItemCreate(BaseModel):
    """Schema for creating a purchase item."""
    
    item_id: UUID = Field(..., description="UUID of the item being purchased")
    quantity: int = Field(..., ge=1, description="Quantity being purchased (minimum 1)")
    unit_cost: Decimal = Field(..., ge=0, description="Cost per unit (minimum 0)")
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100, description="Tax rate percentage (0-100)")
    discount_amount: Optional[Decimal] = Field(None, ge=0, description="Discount amount (minimum 0)")
    condition: ItemCondition = Field(..., description="Condition of the item (A, B, C, or D)")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes (max 500 characters)")
    
    model_config = ConfigDict(use_enum_values=True)

    @field_validator('tax_rate')
    @classmethod
    def validate_tax_rate(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Tax rate must be between 0 and 100')
        return v or Decimal('0')
    
    @field_validator('discount_amount')
    @classmethod
    def validate_discount_amount(cls, v):
        if v is not None and v < 0:
            raise ValueError('Discount amount must be non-negative')
        return v or Decimal('0')


class NewPurchaseRequest(BaseModel):
    """Schema for creating a new purchase transaction."""
    
    supplier_id: UUID = Field(..., description="UUID of the supplier")
    location_id: UUID = Field(..., description="UUID of the location")
    purchase_date: date = Field(..., description="Date of the purchase (YYYY-MM-DD format)")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes (max 1000 characters)")
    reference_number: Optional[str] = Field(None, max_length=50, description="External reference number (max 50 characters)")
    items: List[PurchaseItemCreate] = Field(..., min_length=1, description="List of items being purchased (minimum 1 item)")
    
    @field_validator('items')
    @classmethod
    def validate_items(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one item must be provided')
        if len(v) > 1000:
            raise ValueError('Maximum 1000 items allowed per transaction')
        return v


class PurchaseTransactionLineResponse(BaseModel):
    """Schema for purchase transaction line response."""
    
    id: UUID = Field(..., description="Unique line item identifier")
    line_number: int = Field(..., description="Sequential line number")
    item_id: UUID = Field(..., description="Item identifier")
    description: str = Field(..., description="Line description with condition")
    quantity: Decimal = Field(..., description="Quantity purchased")
    unit_price: Decimal = Field(..., description="Unit cost")
    tax_rate: Decimal = Field(..., description="Tax rate percentage")
    tax_amount: Decimal = Field(..., description="Calculated tax amount")
    discount_amount: Decimal = Field(..., description="Discount amount")
    line_total: Decimal = Field(..., description="Total for this line")
    notes: Optional[str] = Field(None, description="Line item notes")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class PurchaseTransactionDataResponse(BaseModel):
    """Schema for purchase transaction data response."""
    
    id: UUID = Field(..., description="Unique transaction identifier")
    transaction_number: str = Field(..., description="Human-readable transaction number")
    transaction_type: str = Field(..., description="Transaction type (PURCHASE)")
    transaction_date: str = Field(..., description="Purchase date with time")
    customer_id: UUID = Field(..., description="Supplier ID (stored in customer_id field)")
    location_id: UUID = Field(..., description="Location ID")
    status: str = Field(..., description="Transaction status")
    payment_status: str = Field(..., description="Payment status")
    subtotal: Decimal = Field(..., description="Subtotal before discounts and taxes")
    discount_amount: Decimal = Field(..., description="Total discount amount")
    tax_amount: Decimal = Field(..., description="Total tax amount")
    total_amount: Decimal = Field(..., description="Final total amount")
    paid_amount: Decimal = Field(..., description="Amount paid")
    notes: Optional[str] = Field(None, description="Purchase notes")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    transaction_lines: List[PurchaseTransactionLineResponse] = Field(..., description="Array of line items")
    
    model_config = ConfigDict(from_attributes=True)


class PurchaseTransactionResponse(BaseModel):
    """Schema for purchase transaction response."""
    
    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Success message")
    transaction_id: UUID = Field(..., description="Unique identifier for the created transaction")
    transaction_number: str = Field(..., description="Human-readable transaction number")
    data: PurchaseTransactionDataResponse = Field(..., description="Complete transaction details")
    
    model_config = ConfigDict(from_attributes=True)


class PurchaseTransactionCreateInternal(BaseModel):
    """Internal schema for purchase transaction creation."""
    
    supplier_id: UUID
    location_id: UUID
    purchase_date: date
    notes: Optional[str] = None
    reference_number: Optional[str] = None
    items: List[PurchaseItemCreate]
    
    model_config = ConfigDict(from_attributes=True)


# NEW SCHEMAS FOR FILTERING

class PurchaseTransactionFilterRequest(BaseModel):
    """Schema for filtering purchase transactions."""
    
    start_date: Optional[date] = Field(None, description="Start date for filtering (YYYY-MM-DD)")
    end_date: Optional[date] = Field(None, description="End date for filtering (YYYY-MM-DD)")
    supplier_id: Optional[UUID] = Field(None, description="Filter by supplier ID")
    item_ids: Optional[List[UUID]] = Field(None, description="Filter by item IDs (transactions containing these items)")
    status: Optional[str] = Field(None, description="Filter by transaction status")
    payment_status: Optional[str] = Field(None, description="Filter by payment status")
    location_id: Optional[UUID] = Field(None, description="Filter by location ID")
    transaction_number: Optional[str] = Field(None, description="Filter by transaction number (partial match)")
    min_amount: Optional[Decimal] = Field(None, ge=0, description="Minimum transaction amount")
    max_amount: Optional[Decimal] = Field(None, ge=0, description="Maximum transaction amount")
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, values):
        if v and values.get('start_date') and v < values['start_date']:
            raise ValueError('End date must be after start date')
        return v
    
    @field_validator('max_amount')
    @classmethod
    def validate_amount_range(cls, v, values):
        if v and values.get('min_amount') and v < values['min_amount']:
            raise ValueError('Max amount must be greater than min amount')
        return v


class PurchaseTransactionSummary(BaseModel):
    """Schema for purchase transaction summary in list view."""
    
    id: UUID = Field(..., description="Unique transaction identifier")
    transaction_number: str = Field(..., description="Human-readable transaction number")
    transaction_date: datetime = Field(..., description="Purchase date and time")
    supplier_name: Optional[str] = Field(None, description="Supplier name")
    location_name: Optional[str] = Field(None, description="Location name")
    status: str = Field(..., description="Transaction status")
    payment_status: str = Field(..., description="Payment status")
    total_amount: Decimal = Field(..., description="Total transaction amount")
    item_count: int = Field(..., description="Number of items in transaction")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class PurchaseTransactionListResponse(BaseModel):
    """Schema for paginated purchase transaction list response."""
    
    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Response message")
    data: List[PurchaseTransactionSummary] = Field(..., description="List of purchase transactions")
    pagination: Dict[str, Any] = Field(..., description="Pagination metadata")
    
    model_config = ConfigDict(from_attributes=True)


class PaginationParams(BaseModel):
    """Schema for pagination parameters."""
    
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000, description="Maximum records to return")
    sort_by: Optional[str] = Field(None, description="Sort by field (transaction_date, transaction_number, total_amount)")
    sort_order: Optional[str] = Field("desc", description="Sort order (asc, desc)")
    
    model_config = ConfigDict(from_attributes=True)
