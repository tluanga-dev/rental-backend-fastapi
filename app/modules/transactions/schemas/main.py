from typing import Optional, List, Any
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator, computed_field, model_validator
from uuid import UUID

from app.modules.transactions.models import (
    TransactionType,
    TransactionStatus,
    PaymentMethod,
    PaymentStatus,
    RentalPeriodUnit,
    RentalStatus,
    LineItemType,
)


class TransactionHeaderCreate(BaseModel):
    """Schema for creating a new transaction header."""

    transaction_number: str = Field(..., max_length=50, description="Unique transaction number")
    transaction_type: TransactionType = Field(..., description="Transaction type")
    transaction_date: datetime = Field(..., description="Transaction date")
    customer_id: UUID = Field(..., description="Customer ID")
    location_id: UUID = Field(..., description="Location ID")
    sales_person_id: Optional[UUID] = Field(None, description="Sales person ID")
    status: TransactionStatus = Field(
        default=TransactionStatus.PENDING, description="Transaction status"
    )
    reference_transaction_id: Optional[UUID] = Field(None, description="Reference transaction ID")
    notes: Optional[str] = Field(None, description="Additional notes")


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
    notes: Optional[str] = Field(None, description="Additional notes")


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
    customer_advance_balance: Decimal
    due_date: Optional[date]
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
    discount_percentage: Decimal = Field(
        default=Decimal("0.00"), ge=0, le=100, description="Discount percentage"
    )
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=0, description="Discount amount")
    tax_rate: Decimal = Field(default=Decimal("0.00"), ge=0, description="Tax rate")
    rental_period_value: Optional[int] = Field(None, ge=1, description="Rental period value")
    rental_period_unit: Optional[RentalPeriodUnit] = Field(None, description="Rental period unit")
    rental_start_date: Optional[date] = Field(None, description="Rental start date")
    rental_end_date: Optional[date] = Field(None, description="Rental end date")
    current_rental_status: Optional[RentalStatus] = Field(None, description="Current rental status")
    notes: Optional[str] = Field(None, description="Additional notes")

    @field_validator("item_id")
    @classmethod
    def validate_item_id_for_product_service(cls, v, info):
        line_type = info.data.get("line_type")
        if line_type in [LineItemType.PRODUCT, LineItemType.SERVICE]:
            if not v:
                raise ValueError(f"Item ID is required for {line_type.value} lines")
        return v

    @field_validator("rental_period_unit")
    @classmethod
    def validate_rental_period_unit(cls, v, info):
        rental_period_value = info.data.get("rental_period_value")
        if rental_period_value is not None and not v:
            raise ValueError("Rental period unit is required when period value is specified")
        return v

    @field_validator("rental_end_date")
    @classmethod
    def validate_rental_end_date(cls, v, info):
        if v is not None and info.data.get("rental_start_date") is not None:
            if v < info.data.get("rental_start_date"):
                raise ValueError("Rental end date must be after start date")
        return v

    @field_validator("unit_price")
    @classmethod
    def validate_unit_price(cls, v, info):
        line_type = info.data.get("line_type")
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
    discount_percentage: Optional[Decimal] = Field(
        None, ge=0, le=100, description="Discount percentage"
    )
    discount_amount: Optional[Decimal] = Field(None, ge=0, description="Discount amount")
    tax_rate: Optional[Decimal] = Field(None, ge=0, description="Tax rate")
    rental_period_value: Optional[int] = Field(None, ge=1, description="Rental period value")
    rental_period_unit: Optional[RentalPeriodUnit] = Field(None, description="Rental period unit")
    rental_start_date: Optional[date] = Field(None, description="Rental start date")
    rental_end_date: Optional[date] = Field(None, description="Rental end date")
    current_rental_status: Optional[RentalStatus] = Field(None, description="Current rental status")
    notes: Optional[str] = Field(None, description="Additional notes")

    @field_validator("rental_end_date")
    @classmethod
    def validate_rental_end_date(cls, v, info):
        if v is not None and info.data.get("rental_start_date") is not None:
            if v < info.data.get("rental_start_date"):
                raise ValueError("Rental end date must be after start date")
        return v


class TransactionLineResponse(BaseModel):
    """Schema for transaction line response."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    transaction_id: UUID
    line_number: int
    line_type: LineItemType
    item_id: Optional[UUID]
    inventory_unit_id: Optional[UUID]
    description: str
    quantity: Decimal
    unit_price: Decimal
    discount_percentage: Optional[Decimal] = Field(None, alias="discount_percent")
    discount_amount: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    line_total: Decimal
    rental_period_value: Optional[int] = Field(None, alias="rental_period")
    rental_period_unit: Optional[RentalPeriodUnit]
    rental_start_date: Optional[date]
    rental_end_date: Optional[date]
    current_rental_status: Optional[RentalStatus]
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

    discount_percentage: Optional[Decimal] = Field(
        None, ge=0, le=100, description="Discount percentage"
    )
    discount_amount: Optional[Decimal] = Field(None, ge=0, description="Discount amount")
    reason: Optional[str] = Field(None, description="Discount reason")

    @field_validator("discount_percentage")
    @classmethod
    def validate_discount_exclusivity(cls, v, info):
        if v is not None and info.data.get("discount_amount") is not None:
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
    customer_advance_balance: Decimal
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


class TransactionHeaderWithLinesListResponse(BaseModel):
    """Schema for transaction header list response with nested line items."""

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
    customer_advance_balance: Decimal
    due_date: Optional[date]
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

    @field_validator("date_to")
    @classmethod
    def validate_date_range(cls, v, info):
        if v is not None and info.data.get("date_from") is not None:
            if v < info.data.get("date_from"):
                raise ValueError("Date to must be after date from")
        return v

    @field_validator("amount_to")
    @classmethod
    def validate_amount_range(cls, v, info):
        if v is not None and info.data.get("amount_from") is not None:
            if v < info.data.get("amount_from"):
                raise ValueError("Amount to must be greater than amount from")
        return v


# Purchase-specific schemas

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


# Rental-specific schemas

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


class NewRentalRequest(BaseModel):
    """Schema for the new-rental endpoint - matches frontend JSON structure exactly."""
    
    transaction_date: str = Field(..., description="Transaction date in YYYY-MM-DD format")
    customer_id: str = Field(..., description="Customer ID")
    location_id: str = Field(..., description="Location ID")
    payment_method: str = Field(..., description="Payment method")
    payment_reference: Optional[str] = Field("", description="Payment reference")
    notes: Optional[str] = Field("", description="Additional notes")
    items: List[RentalItemCreate] = Field(..., min_length=1, description="Rental items")
    
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
    
    @field_validator("payment_method")
    @classmethod
    def validate_payment_method(cls, v):
        """Validate payment method."""
        valid_methods = ["CASH", "CARD", "BANK_TRANSFER", "CHECK", "ONLINE"]
        if v not in valid_methods:
            raise ValueError(f"Invalid payment method. Must be one of: {', '.join(valid_methods)}")
        return v


class NewRentalResponse(BaseModel):
    """Schema for new-rental response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    success: bool = Field(True, description="Operation success status")
    message: str = Field("Rental created successfully", description="Response message")
    data: dict = Field(..., description="Rental transaction data")
    transaction_id: UUID = Field(..., description="Created transaction ID")
    transaction_number: str = Field(..., description="Generated transaction number")
