from typing import Optional, List, Any
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator, computed_field
from uuid import UUID

from app.modules.transactions.models import (
    TransactionType, TransactionStatus, PaymentMethod, PaymentStatus,
    RentalPeriodUnit, LineItemType
)


class TransactionHeaderCreate(BaseModel):
    """Schema for creating a new transaction header."""
    transaction_number: str = Field(..., max_length=50, description="Unique transaction number")
    transaction_type: TransactionType = Field(..., description="Transaction type")
    transaction_date: datetime = Field(..., description="Transaction date")
    customer_id: UUID = Field(..., description="Customer ID")
    location_id: UUID = Field(..., description="Location ID")
    sales_person_id: Optional[UUID] = Field(None, description="Sales person ID")
    status: TransactionStatus = Field(default=TransactionStatus.DRAFT, description="Transaction status")
    payment_status: PaymentStatus = Field(default=PaymentStatus.PENDING, description="Payment status")
    reference_transaction_id: Optional[UUID] = Field(None, description="Reference transaction ID")
    rental_start_date: Optional[date] = Field(None, description="Rental start date")
    rental_end_date: Optional[date] = Field(None, description="Rental end date")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    @field_validator('rental_end_date')
    @classmethod
    def validate_rental_end_date(cls, v, info):
        if v is not None and info.data.get('rental_start_date') is not None:
            if v < info.data.get('rental_start_date'):
                raise ValueError("Rental end date must be after start date")
        return v
    
    @field_validator('transaction_type')
    @classmethod
    def validate_rental_dates_for_rental_type(cls, v, info):
        if v == TransactionType.RENTAL:
            if not info.data.get('rental_start_date'):
                raise ValueError("Rental start date is required for rental transactions")
            if not info.data.get('rental_end_date'):
                raise ValueError("Rental end date is required for rental transactions")
        return v


class TransactionHeaderUpdate(BaseModel):
    """Schema for updating a transaction header."""
    transaction_type: Optional[TransactionType] = Field(None, description="Transaction type")
    transaction_date: Optional[datetime] = Field(None, description="Transaction date")
    customer_id: Optional[UUID] = Field(None, description="Customer ID")
    location_id: Optional[UUID] = Field(None, description="Location ID")
    sales_person_id: Optional[UUID] = Field(None, description="Sales person ID")
    status: Optional[TransactionStatus] = Field(None, description="Transaction status")
    payment_status: Optional[PaymentStatus] = Field(None, description="Payment status")
    reference_transaction_id: Optional[UUID] = Field(None, description="Reference transaction ID")
    rental_start_date: Optional[date] = Field(None, description="Rental start date")
    rental_end_date: Optional[date] = Field(None, description="Rental end date")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    @field_validator('rental_end_date')
    @classmethod
    def validate_rental_end_date(cls, v, info):
        if v is not None and info.data.get('rental_start_date') is not None:
            if v < info.data.get('rental_start_date'):
                raise ValueError("Rental end date must be after start date")
        return v


class TransactionHeaderResponse(BaseModel):
    """Schema for transaction header response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    transaction_number: str
    transaction_type: TransactionType
    transaction_date: datetime
    customer_id: UUID
    location_id: UUID
    sales_person_id: Optional[UUID]
    status: TransactionStatus
    payment_status: PaymentStatus
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    deposit_amount: Decimal
    reference_transaction_id: Optional[UUID]
    rental_start_date: Optional[date]
    rental_end_date: Optional[date]
    actual_return_date: Optional[date]
    notes: Optional[str]
    payment_method: Optional[PaymentMethod]
    payment_reference: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def display_name(self) -> str:
        return f"{self.transaction_number} - {self.transaction_type.value}"
    
    @computed_field
    @property
    def balance_due(self) -> Decimal:
        return max(self.total_amount - self.paid_amount, Decimal("0.00"))
    
    @computed_field
    @property
    def is_paid_in_full(self) -> bool:
        return self.paid_amount >= self.total_amount
    
    @computed_field
    @property
    def is_rental(self) -> bool:
        return self.transaction_type == TransactionType.RENTAL
    
    @computed_field
    @property
    def is_sale(self) -> bool:
        return self.transaction_type == TransactionType.SALE
    
    @computed_field
    @property
    def rental_days(self) -> int:
        if not self.is_rental or not self.rental_start_date or not self.rental_end_date:
            return 0
        return (self.rental_end_date - self.rental_start_date).days + 1


class TransactionHeaderListResponse(BaseModel):
    """Schema for transaction header list response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    transaction_number: str
    transaction_type: TransactionType
    transaction_date: datetime
    customer_id: UUID
    location_id: UUID
    status: TransactionStatus
    payment_status: PaymentStatus
    total_amount: Decimal
    paid_amount: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def display_name(self) -> str:
        return f"{self.transaction_number} - {self.transaction_type.value}"
    
    @computed_field
    @property
    def balance_due(self) -> Decimal:
        return max(self.total_amount - self.paid_amount, Decimal("0.00"))


class TransactionLineCreate(BaseModel):
    """Schema for creating a new transaction line."""
    line_number: int = Field(..., ge=1, description="Line number")
    line_type: LineItemType = Field(..., description="Line item type")
    description: str = Field(..., max_length=500, description="Line description")
    quantity: Decimal = Field(default=Decimal("1"), ge=0, description="Quantity")
    unit_price: Decimal = Field(default=Decimal("0.00"), description="Unit price")
    item_id: Optional[UUID] = Field(None, description="Item ID")
    inventory_unit_id: Optional[UUID] = Field(None, description="Inventory unit ID")
    discount_percentage: Decimal = Field(default=Decimal("0.00"), ge=0, le=100, description="Discount percentage")
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=0, description="Discount amount")
    tax_rate: Decimal = Field(default=Decimal("0.00"), ge=0, description="Tax rate")
    rental_period_value: Optional[int] = Field(None, ge=1, description="Rental period value")
    rental_period_unit: Optional[RentalPeriodUnit] = Field(None, description="Rental period unit")
    rental_start_date: Optional[date] = Field(None, description="Rental start date")
    rental_end_date: Optional[date] = Field(None, description="Rental end date")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    @field_validator('item_id')
    @classmethod
    def validate_item_id_for_product_service(cls, v, info):
        line_type = info.data.get('line_type')
        if line_type in [LineItemType.PRODUCT, LineItemType.SERVICE]:
            if not v:
                raise ValueError(f"Item ID is required for {line_type.value} lines")
        return v
    
    @field_validator('rental_period_unit')
    @classmethod
    def validate_rental_period_unit(cls, v, info):
        rental_period_value = info.data.get('rental_period_value')
        if rental_period_value is not None and not v:
            raise ValueError("Rental period unit is required when period value is specified")
        return v
    
    @field_validator('rental_end_date')
    @classmethod
    def validate_rental_end_date(cls, v, info):
        if v is not None and info.data.get('rental_start_date') is not None:
            if v < info.data.get('rental_start_date'):
                raise ValueError("Rental end date must be after start date")
        return v
    
    @field_validator('unit_price')
    @classmethod
    def validate_unit_price(cls, v, info):
        line_type = info.data.get('line_type')
        if v < 0 and line_type != LineItemType.DISCOUNT:
            raise ValueError("Unit price cannot be negative except for discount lines")
        return v


class TransactionLineUpdate(BaseModel):
    """Schema for updating a transaction line."""
    line_type: Optional[LineItemType] = Field(None, description="Line item type")
    description: Optional[str] = Field(None, max_length=500, description="Line description")
    quantity: Optional[Decimal] = Field(None, ge=0, description="Quantity")
    unit_price: Optional[Decimal] = Field(None, description="Unit price")
    item_id: Optional[UUID] = Field(None, description="Item ID")
    inventory_unit_id: Optional[UUID] = Field(None, description="Inventory unit ID")
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="Discount percentage")
    discount_amount: Optional[Decimal] = Field(None, ge=0, description="Discount amount")
    tax_rate: Optional[Decimal] = Field(None, ge=0, description="Tax rate")
    rental_period_value: Optional[int] = Field(None, ge=1, description="Rental period value")
    rental_period_unit: Optional[RentalPeriodUnit] = Field(None, description="Rental period unit")
    rental_start_date: Optional[date] = Field(None, description="Rental start date")
    rental_end_date: Optional[date] = Field(None, description="Rental end date")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    @field_validator('rental_end_date')
    @classmethod
    def validate_rental_end_date(cls, v, info):
        if v is not None and info.data.get('rental_start_date') is not None:
            if v < info.data.get('rental_start_date'):
                raise ValueError("Rental end date must be after start date")
        return v


class TransactionLineResponse(BaseModel):
    """Schema for transaction line response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    transaction_id: UUID
    line_number: int
    line_type: LineItemType
    item_id: Optional[UUID]
    inventory_unit_id: Optional[UUID]
    description: str
    quantity: Decimal
    unit_price: Decimal
    discount_percentage: Decimal
    discount_amount: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    line_total: Decimal
    rental_period_value: Optional[int]
    rental_period_unit: Optional[RentalPeriodUnit]
    rental_start_date: Optional[date]
    rental_end_date: Optional[date]
    returned_quantity: Decimal
    return_date: Optional[date]
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def display_name(self) -> str:
        return f"Line {self.line_number}: {self.description}"
    
    @computed_field
    @property
    def remaining_quantity(self) -> Decimal:
        return self.quantity - self.returned_quantity
    
    @computed_field
    @property
    def is_fully_returned(self) -> bool:
        return self.returned_quantity >= self.quantity
    
    @computed_field
    @property
    def is_partially_returned(self) -> bool:
        return 0 < self.returned_quantity < self.quantity
    
    @computed_field
    @property
    def rental_days(self) -> int:
        if not self.rental_start_date or not self.rental_end_date:
            return 0
        return (self.rental_end_date - self.rental_start_date).days + 1
    
    @computed_field
    @property
    def effective_unit_price(self) -> Decimal:
        if self.quantity == 0:
            return Decimal("0.00")
        
        subtotal = self.quantity * self.unit_price
        discounted_amount = subtotal - self.discount_amount
        
        return discounted_amount / self.quantity


class TransactionLineListResponse(BaseModel):
    """Schema for transaction line list response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    transaction_id: UUID
    line_number: int
    line_type: LineItemType
    item_id: Optional[UUID]
    inventory_unit_id: Optional[UUID]
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def display_name(self) -> str:
        return f"Line {self.line_number}: {self.description}"


class PaymentCreate(BaseModel):
    """Schema for creating a payment."""
    amount: Decimal = Field(..., gt=0, description="Payment amount")
    payment_method: PaymentMethod = Field(..., description="Payment method")
    payment_reference: Optional[str] = Field(None, max_length=100, description="Payment reference")
    notes: Optional[str] = Field(None, description="Payment notes")


class RefundCreate(BaseModel):
    """Schema for creating a refund."""
    refund_amount: Decimal = Field(..., gt=0, description="Refund amount")
    reason: str = Field(..., max_length=500, description="Refund reason")
    notes: Optional[str] = Field(None, description="Additional notes")


class StatusUpdate(BaseModel):
    """Schema for updating transaction status."""
    status: TransactionStatus = Field(..., description="New status")
    notes: Optional[str] = Field(None, description="Status update notes")


class DiscountApplication(BaseModel):
    """Schema for applying discount to transaction line."""
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="Discount percentage")
    discount_amount: Optional[Decimal] = Field(None, ge=0, description="Discount amount")
    reason: Optional[str] = Field(None, description="Discount reason")
    
    @field_validator('discount_percentage')
    @classmethod
    def validate_discount_exclusivity(cls, v, info):
        if v is not None and info.data.get('discount_amount') is not None:
            raise ValueError("Cannot apply both percentage and amount discount")
        return v


class ReturnProcessing(BaseModel):
    """Schema for processing returns."""
    return_quantity: Decimal = Field(..., gt=0, description="Return quantity")
    return_date: date = Field(..., description="Return date")
    return_reason: Optional[str] = Field(None, description="Return reason")
    notes: Optional[str] = Field(None, description="Additional notes")


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


class TransactionWithLinesResponse(BaseModel):
    """Schema for transaction with lines response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    transaction_number: str
    transaction_type: TransactionType
    transaction_date: datetime
    customer_id: UUID
    location_id: UUID
    sales_person_id: Optional[UUID]
    status: TransactionStatus
    payment_status: PaymentStatus
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    deposit_amount: Decimal
    reference_transaction_id: Optional[UUID]
    rental_start_date: Optional[date]
    rental_end_date: Optional[date]
    actual_return_date: Optional[date]
    notes: Optional[str]
    payment_method: Optional[PaymentMethod]
    payment_reference: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    transaction_lines: List[TransactionLineResponse] = []
    
    @computed_field
    @property
    def display_name(self) -> str:
        return f"{self.transaction_number} - {self.transaction_type.value}"
    
    @computed_field
    @property
    def balance_due(self) -> Decimal:
        return max(self.total_amount - self.paid_amount, Decimal("0.00"))
    
    @computed_field
    @property
    def is_paid_in_full(self) -> bool:
        return self.paid_amount >= self.total_amount
    
    @computed_field
    @property
    def line_count(self) -> int:
        return len(self.transaction_lines)


class TransactionSummary(BaseModel):
    """Schema for transaction summary."""
    total_transactions: int
    total_amount: Decimal
    total_paid: Decimal
    total_outstanding: Decimal
    transactions_by_status: dict[str, int]
    transactions_by_type: dict[str, int]
    transactions_by_payment_status: dict[str, int]


class TransactionReport(BaseModel):
    """Schema for transaction report."""
    transactions: List[TransactionHeaderListResponse]
    summary: TransactionSummary
    date_range: dict[str, date]


class TransactionSearch(BaseModel):
    """Schema for transaction search."""
    transaction_number: Optional[str] = Field(None, description="Transaction number")
    transaction_type: Optional[TransactionType] = Field(None, description="Transaction type")
    customer_id: Optional[UUID] = Field(None, description="Customer ID")
    location_id: Optional[UUID] = Field(None, description="Location ID")
    sales_person_id: Optional[UUID] = Field(None, description="Sales person ID")
    status: Optional[TransactionStatus] = Field(None, description="Transaction status")
    payment_status: Optional[PaymentStatus] = Field(None, description="Payment status")
    date_from: Optional[date] = Field(None, description="Date from")
    date_to: Optional[date] = Field(None, description="Date to")
    amount_from: Optional[Decimal] = Field(None, ge=0, description="Amount from")
    amount_to: Optional[Decimal] = Field(None, ge=0, description="Amount to")
    
    @field_validator('date_to')
    @classmethod
    def validate_date_range(cls, v, info):
        if v is not None and info.data.get('date_from') is not None:
            if v < info.data.get('date_from'):
                raise ValueError("Date to must be after date from")
        return v
    
    @field_validator('amount_to')
    @classmethod
    def validate_amount_range(cls, v, info):
        if v is not None and info.data.get('amount_from') is not None:
            if v < info.data.get('amount_from'):
                raise ValueError("Amount to must be greater than amount from")
        return v