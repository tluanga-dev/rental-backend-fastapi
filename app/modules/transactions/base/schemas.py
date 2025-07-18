"""
Base Transaction Schemas

Shared schemas and base classes used by all transaction types.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime, date, time
from pydantic import BaseModel, Field, ConfigDict, field_validator, computed_field
from uuid import UUID

from app.modules.transactions.base.models import (
    TransactionType,
    TransactionStatus,
    PaymentMethod,
    PaymentStatus,
    RentalPeriodUnit,
    RentalStatus,
    LineItemType,
)


class TransactionHeaderBase(BaseModel):
    """Base schema for transaction headers."""
    
    transaction_type: TransactionType
    status: TransactionStatus = TransactionStatus.PENDING
    transaction_date: datetime = Field(default_factory=datetime.utcnow)
    due_date: Optional[date] = None
    
    # Parties involved
    customer_id: Optional[str] = None
    location_id: Optional[str] = None
    sales_person_id: Optional[UUID] = None
    
    # Financial information
    currency: str = "USD"
    exchange_rate: Decimal = Decimal("1.0")
    
    # Amount calculations
    subtotal: Decimal = Field(default=Decimal("0"), ge=0)
    discount_amount: Decimal = Field(default=Decimal("0"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0"), ge=0)
    shipping_amount: Decimal = Field(default=Decimal("0"), ge=0)
    total_amount: Decimal = Field(default=Decimal("0"), ge=0)
    paid_amount: Decimal = Field(default=Decimal("0"), ge=0)
    
    # Rental-specific fields
    deposit_amount: Optional[Decimal] = None
    deposit_paid: bool = False
    customer_advance_balance: Decimal = Field(default=Decimal("0"), ge=0)
    
    # Return handling
    reference_transaction_id: Optional[UUID] = None
    
    # Additional information
    notes: Optional[str] = None
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    return_workflow_state: Optional[str] = None
    
    # Delivery fields
    delivery_required: bool = False
    delivery_address: Optional[str] = None
    delivery_date: Optional[date] = None
    delivery_time: Optional[time] = None
    
    # Pickup fields
    pickup_required: bool = False
    pickup_date: Optional[date] = None
    pickup_time: Optional[time] = None
    
    @field_validator("paid_amount")
    def validate_paid_amount(cls, v, values):
        """Validate that paid amount doesn't exceed total amount."""
        if 'total_amount' in values and v > values['total_amount']:
            raise ValueError("Paid amount cannot exceed total amount")
        return v


class TransactionLineBase(BaseModel):
    """Base schema for transaction line items."""
    
    line_number: int = Field(ge=1)
    line_type: LineItemType = LineItemType.PRODUCT
    item_id: Optional[str] = None
    inventory_unit_id: Optional[str] = None
    sku: Optional[str] = None
    
    # Description and categorization
    description: str = Field(min_length=1, max_length=1000)
    category: Optional[str] = None
    
    # Quantity and measurements
    quantity: Decimal = Field(gt=0)
    unit_of_measure: Optional[str] = None
    
    # Pricing information
    unit_price: Decimal = Field(ge=0)
    discount_percent: Decimal = Field(ge=0, le=100)
    discount_amount: Decimal = Field(ge=0)
    tax_rate: Decimal = Field(ge=0)
    tax_amount: Decimal = Field(ge=0)
    line_total: Decimal = Field(ge=0)
    
    # Rental-specific fields
    rental_start_date: Optional[date] = None
    rental_end_date: Optional[date] = None
    rental_period: Optional[int] = None
    rental_period_unit: Optional[RentalPeriodUnit] = None
    current_rental_status: Optional[RentalStatus] = None
    daily_rate: Optional[Decimal] = None
    
    # Inventory and fulfillment
    location_id: Optional[str] = None
    warehouse_location: Optional[str] = None
    
    # Status tracking
    status: str = "PENDING"
    fulfillment_status: str = "PENDING"
    
    # Return handling
    returned_quantity: Decimal = Field(default=Decimal("0"), ge=0)
    return_date: Optional[date] = None
    notes: Optional[str] = None
    return_condition: Optional[str] = Field(default="A", max_length=1)
    return_to_stock: Optional[bool] = True
    inspection_status: Optional[str] = None
    
    @field_validator("returned_quantity")
    def validate_returned_quantity(cls, v, values):
        """Validate that returned quantity doesn't exceed total quantity."""
        if 'quantity' in values and v > values['quantity']:
            raise ValueError("Returned quantity cannot exceed total quantity")
        return v
    
    @field_validator("rental_end_date")
    def validate_rental_dates(cls, v, values):
        """Validate that rental end date is after start date."""
        if v and 'rental_start_date' in values and values['rental_start_date']:
            if v <= values['rental_start_date']:
                raise ValueError("Rental end date must be after start date")
        return v


class TransactionHeaderCreate(TransactionHeaderBase):
    """Schema for creating a new transaction header."""
    
    transaction_lines: List["TransactionLineCreate"] = Field(default_factory=list)
    
    @field_validator("transaction_lines")
    def validate_lines(cls, v):
        """Validate that transaction has at least one line."""
        if not v:
            raise ValueError("Transaction must have at least one line item")
        return v


class TransactionLineCreate(TransactionLineBase):
    """Schema for creating a new transaction line."""
    pass


class TransactionHeaderUpdate(BaseModel):
    """Schema for updating a transaction header."""
    
    status: Optional[TransactionStatus] = None
    due_date: Optional[date] = None
    customer_id: Optional[str] = None
    location_id: Optional[str] = None
    sales_person_id: Optional[UUID] = None
    
    # Financial information
    currency: Optional[str] = None
    exchange_rate: Optional[Decimal] = None
    
    # Amount calculations
    subtotal: Optional[Decimal] = Field(None, ge=0)
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    shipping_amount: Optional[Decimal] = Field(None, ge=0)
    total_amount: Optional[Decimal] = Field(None, ge=0)
    paid_amount: Optional[Decimal] = Field(None, ge=0)
    
    # Rental-specific fields
    deposit_amount: Optional[Decimal] = None
    deposit_paid: Optional[bool] = None
    customer_advance_balance: Optional[Decimal] = Field(None, ge=0)
    
    # Additional information
    notes: Optional[str] = None
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    return_workflow_state: Optional[str] = None
    
    # Delivery fields
    delivery_required: Optional[bool] = None
    delivery_address: Optional[str] = None
    delivery_date: Optional[date] = None
    delivery_time: Optional[time] = None
    
    # Pickup fields
    pickup_required: Optional[bool] = None
    pickup_date: Optional[date] = None
    pickup_time: Optional[time] = None


class TransactionLineUpdate(BaseModel):
    """Schema for updating a transaction line."""
    
    line_type: Optional[LineItemType] = None
    item_id: Optional[str] = None
    inventory_unit_id: Optional[str] = None
    sku: Optional[str] = None
    
    # Description and categorization
    description: Optional[str] = Field(None, min_length=1, max_length=1000)
    category: Optional[str] = None
    
    # Quantity and measurements
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_of_measure: Optional[str] = None
    
    # Pricing information
    unit_price: Optional[Decimal] = Field(None, ge=0)
    discount_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    tax_rate: Optional[Decimal] = Field(None, ge=0)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    line_total: Optional[Decimal] = Field(None, ge=0)
    
    # Rental-specific fields
    rental_start_date: Optional[date] = None
    rental_end_date: Optional[date] = None
    rental_period: Optional[int] = None
    rental_period_unit: Optional[RentalPeriodUnit] = None
    current_rental_status: Optional[RentalStatus] = None
    daily_rate: Optional[Decimal] = None
    
    # Inventory and fulfillment
    location_id: Optional[str] = None
    warehouse_location: Optional[str] = None
    
    # Status tracking
    status: Optional[str] = None
    fulfillment_status: Optional[str] = None
    
    # Return handling
    returned_quantity: Optional[Decimal] = Field(None, ge=0)
    return_date: Optional[date] = None
    notes: Optional[str] = None
    return_condition: Optional[str] = Field(None, max_length=1)
    return_to_stock: Optional[bool] = None
    inspection_status: Optional[str] = None


class TransactionHeaderResponse(TransactionHeaderBase):
    """Schema for transaction header responses."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    transaction_number: str
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    transaction_lines: List["TransactionLineResponse"] = Field(default_factory=list)
    
    @computed_field
    @property
    def balance_due(self) -> Decimal:
        """Calculate outstanding balance."""
        return self.total_amount - self.paid_amount
    
    @computed_field
    @property
    def is_paid(self) -> bool:
        """Check if transaction is fully paid."""
        return self.paid_amount >= self.total_amount
    
    @computed_field
    @property
    def payment_status(self) -> PaymentStatus:
        """Determine payment status."""
        if self.paid_amount == 0:
            return PaymentStatus.PENDING
        elif self.paid_amount >= self.total_amount:
            return PaymentStatus.PAID
        else:
            return PaymentStatus.PARTIAL


class TransactionLineResponse(TransactionLineBase):
    """Schema for transaction line responses."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    transaction_id: UUID
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def extended_price(self) -> Decimal:
        """Calculate extended price before discount."""
        return self.quantity * self.unit_price
    
    @computed_field
    @property
    def net_amount(self) -> Decimal:
        """Calculate net amount after discount but before tax."""
        return self.extended_price - self.discount_amount
    
    @computed_field
    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate quantity not yet returned."""
        return self.quantity - self.returned_quantity
    
    @computed_field
    @property
    def is_fully_returned(self) -> bool:
        """Check if all quantity has been returned."""
        return self.returned_quantity >= self.quantity
    
    @computed_field
    @property
    def is_partially_returned(self) -> bool:
        """Check if some but not all quantity has been returned."""
        return 0 < self.returned_quantity < self.quantity


class TransactionSummary(BaseModel):
    """Summary schema for transaction lists."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    transaction_number: str
    transaction_type: TransactionType
    status: TransactionStatus
    transaction_date: datetime
    customer_id: Optional[str] = None
    total_amount: Decimal
    paid_amount: Decimal
    
    @computed_field
    @property
    def balance_due(self) -> Decimal:
        """Calculate outstanding balance."""
        return self.total_amount - self.paid_amount
    
    @computed_field
    @property
    def payment_status(self) -> PaymentStatus:
        """Determine payment status."""
        if self.paid_amount == 0:
            return PaymentStatus.PENDING
        elif self.paid_amount >= self.total_amount:
            return PaymentStatus.PAID
        else:
            return PaymentStatus.PARTIAL


class TransactionListResponse(BaseModel):
    """Response schema for transaction lists."""
    
    transactions: List[TransactionSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


# Update forward references
TransactionHeaderCreate.model_rebuild()
TransactionHeaderResponse.model_rebuild()
TransactionLineResponse.model_rebuild()