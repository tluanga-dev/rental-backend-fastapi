"""
Purchase Schemas

Pydantic schemas for purchase operations.
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


class PurchaseLineCreate(TransactionLineCreate):
    """Schema for creating a purchase line item."""
    
    supplier_item_code: Optional[str] = None
    received_quantity: Decimal = Field(default=Decimal("0"), ge=0)
    pending_quantity: Decimal = Field(default=Decimal("0"), ge=0)
    inspection_required: bool = False
    inspection_status: Optional[str] = None
    quality_rating: Optional[str] = Field(None, max_length=1)


class PurchaseLineUpdate(BaseModel):
    """Schema for updating a purchase line item."""
    
    description: Optional[str] = None
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    discount_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    tax_rate: Optional[Decimal] = Field(None, ge=0)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    supplier_item_code: Optional[str] = None
    received_quantity: Optional[Decimal] = Field(None, ge=0)
    pending_quantity: Optional[Decimal] = Field(None, ge=0)
    inspection_required: Optional[bool] = None
    inspection_status: Optional[str] = None
    quality_rating: Optional[str] = Field(None, max_length=1)
    notes: Optional[str] = None


class PurchaseLineResponse(TransactionLineResponse):
    """Schema for purchase line item responses."""
    
    supplier_item_code: Optional[str] = None
    received_quantity: Decimal
    pending_quantity: Decimal
    inspection_required: bool
    inspection_status: Optional[str] = None
    quality_rating: Optional[str] = None
    
    @computed_field
    @property
    def remaining_to_receive(self) -> Decimal:
        """Calculate remaining quantity to receive."""
        return self.quantity - self.received_quantity
    
    @computed_field
    @property
    def is_fully_received(self) -> bool:
        """Check if all quantity has been received."""
        return self.received_quantity >= self.quantity
    
    @computed_field
    @property
    def is_partially_received(self) -> bool:
        """Check if some but not all quantity has been received."""
        return 0 < self.received_quantity < self.quantity
    
    @computed_field
    @property
    def is_pending_receipt(self) -> bool:
        """Check if item is pending receipt."""
        return self.pending_quantity > 0


class PurchaseCreate(TransactionHeaderCreate):
    """Schema for creating a new purchase."""
    
    # Purchase-specific fields
    purchase_order_number: Optional[str] = None
    supplier_invoice_number: Optional[str] = None
    supplier_id: Optional[str] = None
    
    # Receiving tracking
    expected_date: Optional[date] = None
    received_date: Optional[date] = None
    
    # Purchase terms
    payment_terms: Optional[str] = None
    freight_terms: Optional[str] = None
    
    # Approval workflow
    approval_status: str = "PENDING"
    approved_by: Optional[str] = None
    approved_date: Optional[date] = None
    
    # Override to use PurchaseLineCreate
    transaction_lines: List[PurchaseLineCreate] = Field(default_factory=list)


class PurchaseUpdate(TransactionHeaderUpdate):
    """Schema for updating a purchase."""
    
    # Purchase-specific fields
    purchase_order_number: Optional[str] = None
    supplier_invoice_number: Optional[str] = None
    supplier_id: Optional[str] = None
    
    # Receiving tracking
    expected_date: Optional[date] = None
    received_date: Optional[date] = None
    
    # Purchase terms
    payment_terms: Optional[str] = None
    freight_terms: Optional[str] = None
    
    # Approval workflow
    approval_status: Optional[str] = None
    approved_by: Optional[str] = None
    approved_date: Optional[date] = None


class PurchaseResponse(TransactionHeaderResponse):
    """Schema for purchase responses."""
    
    # Purchase-specific fields
    purchase_order_number: Optional[str] = None
    supplier_invoice_number: Optional[str] = None
    supplier_id: Optional[str] = None
    
    # Receiving tracking
    expected_date: Optional[date] = None
    received_date: Optional[date] = None
    
    # Purchase terms
    payment_terms: Optional[str] = None
    freight_terms: Optional[str] = None
    
    # Approval workflow
    approval_status: str
    approved_by: Optional[str] = None
    approved_date: Optional[date] = None
    
    # Override to use PurchaseLineResponse
    transaction_lines: List[PurchaseLineResponse] = Field(default_factory=list)
    
    @computed_field
    @property
    def is_fully_received(self) -> bool:
        """Check if all line items are fully received."""
        if not self.transaction_lines:
            return False
        return all(line.is_fully_received for line in self.transaction_lines)
    
    @computed_field
    @property
    def has_pending_receipts(self) -> bool:
        """Check if any line items are pending receipt."""
        return any(line.is_pending_receipt for line in self.transaction_lines)
    
    @computed_field
    @property
    def total_received_value(self) -> Decimal:
        """Calculate total value of received items."""
        return sum(
            line.received_quantity * line.unit_price - line.discount_amount + line.tax_amount
            for line in self.transaction_lines
        )
    
    @computed_field
    @property
    def is_approved(self) -> bool:
        """Check if purchase is approved."""
        return self.approval_status == "APPROVED"


class PurchaseOrderResponse(BaseModel):
    """Schema for purchase order information."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    transaction_number: str
    purchase_order_number: Optional[str] = None
    transaction_date: datetime
    expected_date: Optional[date] = None
    
    # Supplier information
    supplier_id: Optional[str] = None
    supplier_invoice_number: Optional[str] = None
    
    # Financial information
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    
    # Terms
    payment_terms: Optional[str] = None
    freight_terms: Optional[str] = None
    
    # Approval
    approval_status: str
    approved_by: Optional[str] = None
    approved_date: Optional[date] = None
    
    # Line items
    transaction_lines: List[PurchaseLineResponse] = Field(default_factory=list)
    
    @computed_field
    @property
    def balance_due(self) -> Decimal:
        """Calculate outstanding balance."""
        return self.total_amount - self.paid_amount


class PurchaseListResponse(TransactionListResponse):
    """Response schema for purchase lists."""
    
    purchases: List[PurchaseResponse] = Field(alias="transactions")


class PurchaseReportRequest(BaseModel):
    """Schema for purchase report requests."""
    
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    supplier_id: Optional[str] = None
    location_id: Optional[str] = None
    approval_status: Optional[str] = None
    include_returns: bool = False


class PurchaseReportResponse(BaseModel):
    """Schema for purchase report responses."""
    
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    total_purchases: int
    total_spending: Decimal
    average_purchase_amount: Decimal
    total_tax_paid: Decimal
    total_discounts_received: Decimal
    
    # Breakdown by status
    pending_purchases: int
    approved_purchases: int
    completed_purchases: int
    cancelled_purchases: int
    
    # Receiving information
    total_received: int
    total_pending_receipt: int
    
    purchases: List[PurchaseResponse] = Field(default_factory=list)


class ReceivingUpdateRequest(BaseModel):
    """Schema for updating receiving information."""
    
    received_date: date
    line_items: List[Dict[str, Any]] = Field(default_factory=list)  # List of {line_id: UUID, received_quantity: Decimal}


class ApprovalRequest(BaseModel):
    """Schema for purchase approval."""
    
    approved_by: str
    approval_date: date
    notes: Optional[str] = None


class InspectionRequest(BaseModel):
    """Schema for item inspection."""
    
    line_id: UUID
    inspection_status: str
    quality_rating: Optional[str] = Field(None, max_length=1)
    notes: Optional[str] = None