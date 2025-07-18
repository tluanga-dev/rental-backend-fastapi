"""
Sales Schemas

Pydantic schemas for sales operations.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict, computed_field
from uuid import UUID

from app.modules.transactions.base.schemas import (
    TransactionHeaderCreate,
    TransactionHeaderResponse,
    TransactionLineCreate,
    TransactionLineResponse,
    TransactionListResponse,
    TransactionHeaderUpdate,
)


class SaleLineCreate(TransactionLineCreate):
    """Schema for creating a sale line item."""
    
    customer_item_code: Optional[str] = None
    shipped_quantity: Decimal = Field(default=Decimal("0"), ge=0)
    backorder_quantity: Decimal = Field(default=Decimal("0"), ge=0)


class SaleLineUpdate(BaseModel):
    """Schema for updating a sale line item."""
    
    description: Optional[str] = None
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    discount_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    tax_rate: Optional[Decimal] = Field(None, ge=0)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    customer_item_code: Optional[str] = None
    shipped_quantity: Optional[Decimal] = Field(None, ge=0)
    backorder_quantity: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class SaleLineResponse(TransactionLineResponse):
    """Schema for sale line item responses."""
    
    customer_item_code: Optional[str] = None
    shipped_quantity: Decimal
    backorder_quantity: Decimal
    
    @computed_field
    @property
    def remaining_to_ship(self) -> Decimal:
        """Calculate remaining quantity to ship."""
        return self.quantity - self.shipped_quantity
    
    @computed_field
    @property
    def is_fully_shipped(self) -> bool:
        """Check if all quantity has been shipped."""
        return self.shipped_quantity >= self.quantity
    
    @computed_field
    @property
    def is_backordered(self) -> bool:
        """Check if item is on backorder."""
        return self.backorder_quantity > 0


class SaleCreate(TransactionHeaderCreate):
    """Schema for creating a new sale."""
    
    # Sales-specific fields
    invoice_number: Optional[str] = None
    customer_po_number: Optional[str] = None
    sales_rep_commission: Optional[Decimal] = Field(None, ge=0, le=100)
    customer_discount_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    
    # Delivery tracking
    shipped_date: Optional[date] = None
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    
    # Customer service
    warranty_period_days: Optional[int] = Field(None, ge=0)
    
    # Override to use SaleLineCreate
    transaction_lines: List[SaleLineCreate] = Field(default_factory=list)


class SaleUpdate(TransactionHeaderUpdate):
    """Schema for updating a sale."""
    
    # Sales-specific fields
    invoice_number: Optional[str] = None
    customer_po_number: Optional[str] = None
    sales_rep_commission: Optional[Decimal] = Field(None, ge=0, le=100)
    customer_discount_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    
    # Delivery tracking
    shipped_date: Optional[date] = None
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    
    # Customer service
    warranty_period_days: Optional[int] = Field(None, ge=0)


class SaleResponse(TransactionHeaderResponse):
    """Schema for sale responses."""
    
    # Sales-specific fields
    invoice_number: Optional[str] = None
    customer_po_number: Optional[str] = None
    sales_rep_commission: Optional[Decimal] = None
    customer_discount_percent: Optional[Decimal] = None
    
    # Delivery tracking
    shipped_date: Optional[date] = None
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    
    # Customer service
    warranty_period_days: Optional[int] = None
    
    # Override to use SaleLineResponse
    transaction_lines: List[SaleLineResponse] = Field(default_factory=list)
    
    @computed_field
    @property
    def is_fully_shipped(self) -> bool:
        """Check if all line items are fully shipped."""
        if not self.transaction_lines:
            return False
        return all(line.is_fully_shipped for line in self.transaction_lines)
    
    @computed_field
    @property
    def has_backorders(self) -> bool:
        """Check if any line items are on backorder."""
        return any(line.is_backordered for line in self.transaction_lines)
    
    @computed_field
    @property
    def total_shipped_value(self) -> Decimal:
        """Calculate total value of shipped items."""
        return sum(
            line.shipped_quantity * line.unit_price - line.discount_amount + line.tax_amount
            for line in self.transaction_lines
        )


class SaleInvoiceResponse(BaseModel):
    """Schema for sale invoice information."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    transaction_number: str
    invoice_number: Optional[str] = None
    transaction_date: datetime
    due_date: Optional[date] = None
    
    # Customer information
    customer_id: Optional[str] = None
    customer_po_number: Optional[str] = None
    
    # Financial information
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    
    # Delivery information
    delivery_required: bool
    delivery_address: Optional[str] = None
    delivery_date: Optional[date] = None
    shipped_date: Optional[date] = None
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    
    # Line items
    transaction_lines: List[SaleLineResponse] = Field(default_factory=list)
    
    @computed_field
    @property
    def balance_due(self) -> Decimal:
        """Calculate outstanding balance."""
        return self.total_amount - self.paid_amount


class SaleListResponse(TransactionListResponse):
    """Response schema for sale lists."""
    
    sales: List[SaleResponse] = Field(alias="transactions")


class SalesReportRequest(BaseModel):
    """Schema for sales report requests."""
    
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    customer_id: Optional[str] = None
    location_id: Optional[str] = None
    sales_person_id: Optional[UUID] = None
    include_returns: bool = False


class SalesReportResponse(BaseModel):
    """Schema for sales report responses."""
    
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    total_sales: int
    total_revenue: Decimal
    total_cost: Decimal
    gross_profit: Decimal
    average_sale_amount: Decimal
    total_tax_collected: Decimal
    total_discounts_given: Decimal
    
    # Breakdown by status
    pending_sales: int
    completed_sales: int
    cancelled_sales: int
    
    # Shipping information
    total_shipped: int
    total_backorders: int
    
    sales: List[SaleResponse] = Field(default_factory=list)
    
    @computed_field
    @property
    def gross_margin_percent(self) -> Optional[Decimal]:
        """Calculate gross margin percentage."""
        if self.total_revenue == 0:
            return None
        return (self.gross_profit / self.total_revenue) * 100


class ShippingUpdateRequest(BaseModel):
    """Schema for updating shipping information."""
    
    shipped_date: date
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    line_items: List[Dict[str, Any]] = Field(default_factory=list)  # List of {line_id: UUID, shipped_quantity: Decimal}


class BackorderRequest(BaseModel):
    """Schema for managing backorders."""
    
    line_id: UUID
    backorder_quantity: Decimal = Field(gt=0)
    expected_date: Optional[date] = None
    reason: Optional[str] = None