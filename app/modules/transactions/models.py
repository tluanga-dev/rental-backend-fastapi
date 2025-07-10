from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy import Column, String, Numeric, Boolean, Text, DateTime, Date, ForeignKey, Integer, Index
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

from app.db.base import BaseModel, UUIDType

if TYPE_CHECKING:
    from app.modules.customers.models import Customer
    from app.modules.master_data.locations.models import Location
    # from app.modules.auth.models import User  # Temporarily disabled
    from app.modules.inventory.models import Item, InventoryUnit


class TransactionType(str, Enum):
    """Transaction type enumeration."""
    SALE = "SALE"
    RENTAL = "RENTAL"
    RETURN = "RETURN"
    EXCHANGE = "EXCHANGE"
    REFUND = "REFUND"
    ADJUSTMENT = "ADJUSTMENT"
    PURCHASE = "PURCHASE"


class TransactionStatus(str, Enum):
    """Transaction status enumeration."""
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class PaymentMethod(str, Enum):
    """Payment method enumeration."""
    CASH = "CASH"
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    BANK_TRANSFER = "BANK_TRANSFER"
    CHECK = "CHECK"
    STORE_CREDIT = "STORE_CREDIT"
    DEPOSIT = "DEPOSIT"
    OTHER = "OTHER"


class PaymentStatus(str, Enum):
    """Payment status enumeration."""
    PENDING = "PENDING"
    PAID = "PAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    OVERDUE = "OVERDUE"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"


class RentalPeriodUnit(str, Enum):
    """Rental period unit enumeration."""
    HOUR = "HOUR"
    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"
    YEAR = "YEAR"


class LineItemType(str, Enum):
    """Line item type enumeration."""
    PRODUCT = "PRODUCT"
    SERVICE = "SERVICE"
    FEE = "FEE"
    DISCOUNT = "DISCOUNT"
    TAX = "TAX"
    DEPOSIT = "DEPOSIT"
    LATE_FEE = "LATE_FEE"
    DAMAGE_FEE = "DAMAGE_FEE"
    REFUND = "REFUND"


class TransactionHeader(BaseModel):
    """
    Transaction header model for managing transactions.
    
    Attributes:
        transaction_number: Unique transaction number
        transaction_type: Type of transaction
        transaction_date: Date of transaction
        customer_id: Customer ID
        location_id: Location ID
        sales_person_id: Sales person ID
        status: Transaction status
        payment_status: Payment status
        subtotal: Subtotal amount
        discount_amount: Discount amount
        tax_amount: Tax amount
        total_amount: Total amount
        paid_amount: Paid amount
        deposit_amount: Deposit amount
        reference_transaction_id: Reference transaction ID
        rental_start_date: Rental start date
        rental_end_date: Rental end date
        actual_return_date: Actual return date
        notes: Additional notes
        payment_method: Payment method
        payment_reference: Payment reference
        customer: Customer relationship
        location: Location relationship
        sales_person: Sales person relationship
        reference_transaction: Reference transaction relationship
        transaction_lines: Transaction lines
    """
    
    __tablename__ = "transaction_headers"
    
    transaction_number = Column(String(50), nullable=False, unique=True, index=True, comment="Unique transaction number")
    transaction_type = Column(String(20), nullable=False, comment="Transaction type")
    transaction_date = Column(DateTime, nullable=False, comment="Transaction date")
    customer_id = Column(UUIDType(), nullable=False, comment="Customer ID")  # ForeignKey("customers.id") - temporarily disabled
    location_id = Column(UUIDType(), nullable=False, comment="Location ID")  # ForeignKey("locations.id") - temporarily disabled
    sales_person_id = Column(UUIDType(), nullable=True, comment="Sales person ID")  # ForeignKey("users.id") - temporarily disabled
    status = Column(String(20), nullable=False, default=TransactionStatus.DRAFT.value, comment="Transaction status")
    payment_status = Column(String(20), nullable=False, default=PaymentStatus.PENDING.value, comment="Payment status")
    subtotal = Column(Numeric(12, 2), nullable=False, default=0.00, comment="Subtotal amount")
    discount_amount = Column(Numeric(12, 2), nullable=False, default=0.00, comment="Discount amount")
    tax_amount = Column(Numeric(12, 2), nullable=False, default=0.00, comment="Tax amount")
    total_amount = Column(Numeric(12, 2), nullable=False, default=0.00, comment="Total amount")
    paid_amount = Column(Numeric(12, 2), nullable=False, default=0.00, comment="Paid amount")
    deposit_amount = Column(Numeric(12, 2), nullable=False, default=0.00, comment="Deposit amount")
    reference_transaction_id = Column(UUIDType(), ForeignKey("transaction_headers.id"), nullable=True, comment="Reference transaction ID")
    rental_start_date = Column(Date, nullable=True, comment="Rental start date")
    rental_end_date = Column(Date, nullable=True, comment="Rental end date")
    actual_return_date = Column(Date, nullable=True, comment="Actual return date")
    notes = Column(Text, nullable=True, comment="Additional notes")
    payment_method = Column(String(20), nullable=True, comment="Payment method")
    payment_reference = Column(String(100), nullable=True, comment="Payment reference")
    
    # Relationships
    # customer = relationship("Customer", back_populates="transactions", lazy="select")  # Temporarily disabled
    # location = relationship("Location", back_populates="transactions", lazy="select")  # Temporarily disabled
    # sales_person = relationship("User", back_populates="transactions", lazy="select")  # Temporarily disabled
    reference_transaction = relationship("TransactionHeader", remote_side="TransactionHeader.id", lazy="select")
    transaction_lines = relationship("TransactionLine", back_populates="transaction", lazy="select", cascade="all, delete-orphan")
    rental_returns = relationship("RentalReturn", back_populates="rental_transaction", lazy="select")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_transaction_number', 'transaction_number'),
        Index('idx_transaction_type', 'transaction_type'),
        Index('idx_transaction_date', 'transaction_date'),
        Index('idx_transaction_customer', 'customer_id'),
        Index('idx_transaction_location', 'location_id'),
        Index('idx_transaction_sales_person', 'sales_person_id'),
        Index('idx_transaction_status', 'status'),
        Index('idx_transaction_payment_status', 'payment_status'),
        Index('idx_transaction_rental_dates', 'rental_start_date', 'rental_end_date'),
# Removed is_active index - column is inherited from BaseModel
    )
    
    def __init__(
        self,
        transaction_number: str,
        transaction_type: TransactionType,
        transaction_date: datetime,
        customer_id: str,
        location_id: str,
        sales_person_id: Optional[str] = None,
        status: TransactionStatus = TransactionStatus.DRAFT,
        payment_status: PaymentStatus = PaymentStatus.PENDING,
        subtotal: Decimal = Decimal("0.00"),
        discount_amount: Decimal = Decimal("0.00"),
        tax_amount: Decimal = Decimal("0.00"),
        total_amount: Decimal = Decimal("0.00"),
        paid_amount: Decimal = Decimal("0.00"),
        deposit_amount: Decimal = Decimal("0.00"),
        reference_transaction_id: Optional[str] = None,
        rental_start_date: Optional[date] = None,
        rental_end_date: Optional[date] = None,
        notes: Optional[str] = None,
        payment_method: Optional[PaymentMethod] = None,
        payment_reference: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize a Transaction Header.
        
        Args:
            transaction_number: Unique transaction number
            transaction_type: Type of transaction
            transaction_date: Date of transaction
            customer_id: Customer ID
            location_id: Location ID
            sales_person_id: Sales person ID
            status: Transaction status
            payment_status: Payment status
            subtotal: Subtotal amount
            discount_amount: Discount amount
            tax_amount: Tax amount
            total_amount: Total amount
            paid_amount: Paid amount
            deposit_amount: Deposit amount
            reference_transaction_id: Reference transaction ID
            rental_start_date: Rental start date
            rental_end_date: Rental end date
            notes: Additional notes
            payment_method: Payment method
            payment_reference: Payment reference
            **kwargs: Additional BaseModel fields
        """
        super().__init__(**kwargs)
        self.transaction_number = transaction_number
        self.transaction_type = transaction_type.value if isinstance(transaction_type, TransactionType) else transaction_type
        self.transaction_date = transaction_date
        self.customer_id = customer_id
        self.location_id = location_id
        self.sales_person_id = sales_person_id
        self.status = status.value if isinstance(status, TransactionStatus) else status
        self.payment_status = payment_status.value if isinstance(payment_status, PaymentStatus) else payment_status
        self.subtotal = subtotal
        self.discount_amount = discount_amount
        self.tax_amount = tax_amount
        self.total_amount = total_amount
        self.paid_amount = paid_amount
        self.deposit_amount = deposit_amount
        self.reference_transaction_id = reference_transaction_id
        self.rental_start_date = rental_start_date
        self.rental_end_date = rental_end_date
        self.notes = notes
        self.payment_method = payment_method.value if isinstance(payment_method, PaymentMethod) else payment_method
        self.payment_reference = payment_reference
        self._validate()
    
    def _validate(self):
        """Validate transaction header business rules."""
        # Number validation
        if not self.transaction_number or not self.transaction_number.strip():
            raise ValueError("Transaction number cannot be empty")
        
        if len(self.transaction_number) > 50:
            raise ValueError("Transaction number cannot exceed 50 characters")
        
        # Type validation
        if self.transaction_type not in [tt.value for tt in TransactionType]:
            raise ValueError(f"Invalid transaction type: {self.transaction_type}")
        
        # Status validation
        if self.status not in [ts.value for ts in TransactionStatus]:
            raise ValueError(f"Invalid transaction status: {self.status}")
        
        # Payment status validation
        if self.payment_status not in [ps.value for ps in PaymentStatus]:
            raise ValueError(f"Invalid payment status: {self.payment_status}")
        
        # Amount validation
        if self.subtotal < 0:
            raise ValueError("Subtotal cannot be negative")
        
        if self.discount_amount < 0:
            raise ValueError("Discount amount cannot be negative")
        
        if self.tax_amount < 0:
            raise ValueError("Tax amount cannot be negative")
        
        if self.total_amount < 0:
            raise ValueError("Total amount cannot be negative")
        
        if self.paid_amount < 0:
            raise ValueError("Paid amount cannot be negative")
        
        if self.deposit_amount < 0:
            raise ValueError("Deposit amount cannot be negative")
        
        # Rental date validation
        if self.transaction_type == TransactionType.RENTAL.value:
            if not self.rental_start_date:
                raise ValueError("Rental start date is required for rental transactions")
            if not self.rental_end_date:
                raise ValueError("Rental end date is required for rental transactions")
            if self.rental_end_date < self.rental_start_date:
                raise ValueError("Rental end date must be after start date")
        
        # Payment method validation
        if self.payment_method and self.payment_method not in [pm.value for pm in PaymentMethod]:
            raise ValueError(f"Invalid payment method: {self.payment_method}")
        
        # Payment reference validation
        if self.payment_reference and len(self.payment_reference) > 100:
            raise ValueError("Payment reference cannot exceed 100 characters")
    
    def can_transition_to(self, new_status: TransactionStatus) -> bool:
        """Check if status transition is valid."""
        valid_transitions = {
            TransactionStatus.DRAFT.value: [
                TransactionStatus.PENDING.value,
                TransactionStatus.CANCELLED.value
            ],
            TransactionStatus.PENDING.value: [
                TransactionStatus.CONFIRMED.value,
                TransactionStatus.CANCELLED.value
            ],
            TransactionStatus.CONFIRMED.value: [
                TransactionStatus.IN_PROGRESS.value,
                TransactionStatus.CANCELLED.value
            ],
            TransactionStatus.IN_PROGRESS.value: [
                TransactionStatus.COMPLETED.value,
                TransactionStatus.CANCELLED.value
            ],
            TransactionStatus.COMPLETED.value: [
                TransactionStatus.REFUNDED.value
            ],
            TransactionStatus.CANCELLED.value: [],
            TransactionStatus.REFUNDED.value: []
        }
        
        return new_status.value in valid_transitions.get(self.status, [])
    
    def update_status(self, new_status: TransactionStatus, updated_by: Optional[str] = None):
        """Update transaction status with validation."""
        if not self.can_transition_to(new_status):
            raise ValueError(f"Cannot transition from {self.status} to {new_status.value}")
        
        self.status = new_status.value
        self.updated_by = updated_by
    
    def calculate_totals(self):
        """Recalculate transaction totals from lines."""
        if not self.transaction_lines:
            self.subtotal = Decimal("0.00")
            self.discount_amount = Decimal("0.00")
            self.tax_amount = Decimal("0.00")
            self.deposit_amount = Decimal("0.00")
            self.total_amount = Decimal("0.00")
            return
        
        # Calculate subtotal from product/service lines
        self.subtotal = sum(
            line.line_total for line in self.transaction_lines
            if line.line_type in [LineItemType.PRODUCT.value, LineItemType.SERVICE.value]
        )
        
        # Calculate discount from discount lines
        self.discount_amount = abs(sum(
            line.line_total for line in self.transaction_lines
            if line.line_type == LineItemType.DISCOUNT.value
        ))
        
        # Calculate tax from tax lines
        self.tax_amount = sum(
            line.line_total for line in self.transaction_lines
            if line.line_type == LineItemType.TAX.value
        )
        
        # Calculate deposit amount
        self.deposit_amount = sum(
            line.line_total for line in self.transaction_lines
            if line.line_type == LineItemType.DEPOSIT.value
        )
        
        # Calculate total
        self.total_amount = self.subtotal - self.discount_amount + self.tax_amount
    
    def apply_payment(
        self,
        amount: Decimal,
        payment_method: PaymentMethod,
        payment_reference: Optional[str] = None,
        updated_by: Optional[str] = None
    ):
        """Apply payment to transaction."""
        if amount <= 0:
            raise ValueError("Payment amount must be positive")
        
        if self.status not in [TransactionStatus.PENDING.value, TransactionStatus.CONFIRMED.value]:
            raise ValueError(f"Cannot apply payment to transaction in {self.status} status")
        
        self.paid_amount += amount
        self.payment_method = payment_method.value
        self.payment_reference = payment_reference
        
        # Update payment status
        if self.paid_amount >= self.total_amount:
            self.payment_status = PaymentStatus.PAID.value
        elif self.paid_amount > 0:
            self.payment_status = PaymentStatus.PARTIALLY_PAID.value
        
        self.updated_by = updated_by
    
    def cancel_transaction(self, reason: str, cancelled_by: Optional[str] = None):
        """Cancel the transaction."""
        if self.status == TransactionStatus.COMPLETED.value:
            raise ValueError("Cannot cancel completed transaction. Use refund instead.")
        
        if self.status == TransactionStatus.CANCELLED.value:
            raise ValueError("Transaction is already cancelled")
        
        self.status = TransactionStatus.CANCELLED.value
        self.payment_status = PaymentStatus.CANCELLED.value
        
        # Add cancellation note
        cancel_note = f"\n[CANCELLED] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: {reason}"
        self.notes = (self.notes or "") + cancel_note
        
        self.updated_by = cancelled_by
    
    def process_refund(
        self,
        refund_amount: Decimal,
        reason: str,
        refunded_by: Optional[str] = None
    ):
        """Process refund for completed transaction."""
        if self.status != TransactionStatus.COMPLETED.value:
            raise ValueError("Can only refund completed transactions")
        
        if refund_amount <= 0:
            raise ValueError("Refund amount must be positive")
        
        if refund_amount > self.paid_amount:
            raise ValueError("Refund amount cannot exceed paid amount")
        
        self.paid_amount -= refund_amount
        self.status = TransactionStatus.REFUNDED.value
        self.payment_status = PaymentStatus.REFUNDED.value
        
        # Add refund note
        refund_note = f"\n[REFUNDED] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: ${refund_amount} - {reason}"
        self.notes = (self.notes or "") + refund_note
        
        self.updated_by = refunded_by
    
    def mark_as_overdue(self, updated_by: Optional[str] = None):
        """Mark transaction payment as overdue."""
        if self.payment_status == PaymentStatus.PAID.value:
            raise ValueError("Cannot mark paid transaction as overdue")
        
        if self.status == TransactionStatus.CANCELLED.value:
            raise ValueError("Cannot mark cancelled transaction as overdue")
        
        self.payment_status = PaymentStatus.OVERDUE.value
        self.updated_by = updated_by
    
    def complete_rental_return(
        self,
        actual_return_date: date,
        updated_by: Optional[str] = None
    ):
        """Complete rental return."""
        if self.transaction_type != TransactionType.RENTAL.value:
            raise ValueError("Can only process return for rental transactions")
        
        if self.status != TransactionStatus.IN_PROGRESS.value:
            raise ValueError("Can only process return for in-progress rentals")
        
        self.actual_return_date = actual_return_date
        self.status = TransactionStatus.COMPLETED.value
        self.updated_by = updated_by
    
    def is_rental(self) -> bool:
        """Check if this is a rental transaction."""
        return self.transaction_type == TransactionType.RENTAL.value
    
    def is_sale(self) -> bool:
        """Check if this is a sale transaction."""
        return self.transaction_type == TransactionType.SALE.value
    
    def is_paid_in_full(self) -> bool:
        """Check if transaction is paid in full."""
        return self.paid_amount >= self.total_amount
    
    @property
    def balance_due(self) -> Decimal:
        """Calculate balance due."""
        return max(self.total_amount - self.paid_amount, Decimal("0.00"))
    
    @property
    def rental_days(self) -> int:
        """Calculate rental days for rental transactions."""
        if not self.is_rental() or not self.rental_start_date or not self.rental_end_date:
            return 0
        return (self.rental_end_date - self.rental_start_date).days + 1
    
    @property
    def display_name(self) -> str:
        """Get transaction display name."""
        return f"{self.transaction_number} - {self.transaction_type}"
    
    def __str__(self) -> str:
        """String representation of transaction."""
        return f"Transaction({self.transaction_number}: {self.transaction_type} - ${self.total_amount})"
    
    def __repr__(self) -> str:
        """Developer representation of transaction."""
        return (
            f"TransactionHeader(id={self.id}, number='{self.transaction_number}', "
            f"type='{self.transaction_type}', status='{self.status}', "
            f"total=${self.total_amount}, active={self.is_active})"
        )


class TransactionLine(BaseModel):
    """
    Transaction line model for managing transaction line items.
    
    Attributes:
        transaction_id: Transaction ID
        line_number: Line number
        line_type: Line item type
        item_id: Item ID
        inventory_unit_id: Inventory unit ID
        description: Line description
        quantity: Quantity
        unit_price: Unit price
        discount_percentage: Discount percentage
        discount_amount: Discount amount
        tax_rate: Tax rate
        tax_amount: Tax amount
        line_total: Line total
        rental_period_value: Rental period value
        rental_period_unit: Rental period unit
        rental_start_date: Rental start date
        rental_end_date: Rental end date
        returned_quantity: Returned quantity
        return_date: Return date
        notes: Additional notes
        transaction: Transaction relationship
        item: Item relationship
        inventory_unit: Inventory unit relationship
    """
    
    __tablename__ = "transaction_lines"
    
    transaction_id = Column(UUIDType(), ForeignKey("transaction_headers.id"), nullable=False, comment="Transaction ID")
    line_number = Column(Integer, nullable=False, comment="Line number")
    line_type = Column(String(20), nullable=False, comment="Line item type")
    item_id = Column(UUIDType(), ForeignKey("items.id"), nullable=True, comment="Item ID")
    inventory_unit_id = Column(UUIDType(), ForeignKey("inventory_units.id"), nullable=True, comment="Inventory unit ID")
    description = Column(String(500), nullable=False, comment="Line description")
    quantity = Column(Numeric(10, 2), nullable=False, default=1, comment="Quantity")
    unit_price = Column(Numeric(10, 2), nullable=False, default=0.00, comment="Unit price")
    discount_percentage = Column(Numeric(5, 2), nullable=False, default=0.00, comment="Discount percentage")
    discount_amount = Column(Numeric(10, 2), nullable=False, default=0.00, comment="Discount amount")
    tax_rate = Column(Numeric(5, 2), nullable=False, default=0.00, comment="Tax rate")
    tax_amount = Column(Numeric(10, 2), nullable=False, default=0.00, comment="Tax amount")
    line_total = Column(Numeric(10, 2), nullable=False, default=0.00, comment="Line total")
    rental_period_value = Column(Integer, nullable=True, comment="Rental period value")
    rental_period_unit = Column(String(10), nullable=True, comment="Rental period unit")
    rental_start_date = Column(Date, nullable=True, comment="Rental start date")
    rental_end_date = Column(Date, nullable=True, comment="Rental end date")
    returned_quantity = Column(Numeric(10, 2), nullable=False, default=0, comment="Returned quantity")
    return_date = Column(Date, nullable=True, comment="Return date")
    notes = Column(Text, nullable=True, comment="Additional notes")
    
    # Relationships
    transaction = relationship("TransactionHeader", back_populates="transaction_lines", lazy="select")
    # item = relationship("Item", back_populates="transaction_lines", lazy="select")  # Temporarily disabled
    # inventory_unit = relationship("InventoryUnit", back_populates="transaction_lines", lazy="select")  # Temporarily disabled
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_transaction_line_transaction', 'transaction_id'),
        Index('idx_transaction_line_number', 'transaction_id', 'line_number'),
        Index('idx_transaction_line_type', 'line_type'),
        Index('idx_transaction_line_item', 'item_id'),
        Index('idx_transaction_line_inventory_unit', 'inventory_unit_id'),
        Index('idx_transaction_line_rental_dates', 'rental_start_date', 'rental_end_date'),
# Removed is_active index - column is inherited from BaseModel
    )
    
    def __init__(
        self,
        transaction_id: str,
        line_number: int,
        line_type: LineItemType,
        description: str,
        quantity: Decimal = Decimal("1"),
        unit_price: Decimal = Decimal("0.00"),
        item_id: Optional[str] = None,
        inventory_unit_id: Optional[str] = None,
        discount_percentage: Decimal = Decimal("0.00"),
        discount_amount: Decimal = Decimal("0.00"),
        tax_rate: Decimal = Decimal("0.00"),
        tax_amount: Decimal = Decimal("0.00"),
        line_total: Decimal = Decimal("0.00"),
        rental_period_value: Optional[int] = None,
        rental_period_unit: Optional[RentalPeriodUnit] = None,
        rental_start_date: Optional[date] = None,
        rental_end_date: Optional[date] = None,
        returned_quantity: Decimal = Decimal("0"),
        return_date: Optional[date] = None,
        notes: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize a Transaction Line.
        
        Args:
            transaction_id: Transaction ID
            line_number: Line number
            line_type: Line item type
            description: Line description
            quantity: Quantity
            unit_price: Unit price
            item_id: Item ID
            inventory_unit_id: Inventory unit ID
            discount_percentage: Discount percentage
            discount_amount: Discount amount
            tax_rate: Tax rate
            tax_amount: Tax amount
            line_total: Line total
            rental_period_value: Rental period value
            rental_period_unit: Rental period unit
            rental_start_date: Rental start date
            rental_end_date: Rental end date
            returned_quantity: Returned quantity
            return_date: Return date
            notes: Additional notes
            **kwargs: Additional BaseModel fields
        """
        super().__init__(**kwargs)
        self.transaction_id = transaction_id
        self.line_number = line_number
        self.line_type = line_type.value if isinstance(line_type, LineItemType) else line_type
        self.description = description
        self.quantity = quantity
        self.unit_price = unit_price
        self.item_id = item_id
        self.inventory_unit_id = inventory_unit_id
        self.discount_percentage = discount_percentage
        self.discount_amount = discount_amount
        self.tax_rate = tax_rate
        self.tax_amount = tax_amount
        self.line_total = line_total
        self.rental_period_value = rental_period_value
        self.rental_period_unit = rental_period_unit.value if isinstance(rental_period_unit, RentalPeriodUnit) else rental_period_unit
        self.rental_start_date = rental_start_date
        self.rental_end_date = rental_end_date
        self.returned_quantity = returned_quantity
        self.return_date = return_date
        self.notes = notes
        self._validate()
    
    def _validate(self):
        """Validate transaction line business rules."""
        # Line number validation
        if self.line_number < 1:
            raise ValueError("Line number must be positive")
        
        # Line type validation
        if self.line_type not in [lit.value for lit in LineItemType]:
            raise ValueError(f"Invalid line item type: {self.line_type}")
        
        # Description validation
        if not self.description or not self.description.strip():
            raise ValueError("Description cannot be empty")
        
        if len(self.description) > 500:
            raise ValueError("Description cannot exceed 500 characters")
        
        # Quantity validation
        if self.quantity < 0:
            raise ValueError("Quantity cannot be negative")
        
        # Unit price validation (allow negative for discount lines)
        if self.unit_price < 0 and self.line_type != LineItemType.DISCOUNT.value:
            raise ValueError("Unit price cannot be negative")
        
        # Discount validation
        if self.discount_percentage < 0 or self.discount_percentage > 100:
            raise ValueError("Discount percentage must be between 0 and 100")
        
        if self.discount_amount < 0:
            raise ValueError("Discount amount cannot be negative")
        
        # Tax validation
        if self.tax_rate < 0:
            raise ValueError("Tax rate cannot be negative")
        
        if self.tax_amount < 0:
            raise ValueError("Tax amount cannot be negative")
        
        # Returned quantity validation
        if self.returned_quantity < 0:
            raise ValueError("Returned quantity cannot be negative")
        
        if self.returned_quantity > self.quantity:
            raise ValueError("Returned quantity cannot exceed ordered quantity")
        
        # Product/service line validation
        if self.line_type in [LineItemType.PRODUCT.value, LineItemType.SERVICE.value]:
            if not self.item_id:
                raise ValueError(f"Item ID is required for {self.line_type} lines")
        
        # Rental period validation
        if self.rental_period_value is not None:
            if self.rental_period_value < 1:
                raise ValueError("Rental period value must be positive")
            if not self.rental_period_unit:
                raise ValueError("Rental period unit is required when period value is specified")
        
        # Rental period unit validation
        if self.rental_period_unit and self.rental_period_unit not in [rpu.value for rpu in RentalPeriodUnit]:
            raise ValueError(f"Invalid rental period unit: {self.rental_period_unit}")
        
        # Rental date validation
        if self.rental_start_date and self.rental_end_date:
            if self.rental_end_date < self.rental_start_date:
                raise ValueError("Rental end date must be after start date")
    
    def calculate_line_total(self):
        """Calculate line total based on quantity, price, discount, and tax."""
        # Base calculation
        subtotal = self.quantity * self.unit_price
        
        # Apply discount
        if self.discount_percentage > 0:
            self.discount_amount = subtotal * (self.discount_percentage / 100)
        
        discounted_amount = subtotal - self.discount_amount
        
        # Calculate tax
        if self.tax_rate > 0:
            self.tax_amount = discounted_amount * (self.tax_rate / 100)
        
        # Calculate final total
        self.line_total = discounted_amount + self.tax_amount
        
        # For discount lines, make total negative
        if self.line_type == LineItemType.DISCOUNT.value:
            self.line_total = -abs(self.line_total)
    
    def apply_discount(
        self,
        discount_percentage: Optional[Decimal] = None,
        discount_amount: Optional[Decimal] = None,
        updated_by: Optional[str] = None
    ):
        """Apply discount to line item."""
        if discount_percentage is not None and discount_amount is not None:
            raise ValueError("Cannot apply both percentage and amount discount")
        
        if discount_percentage is not None:
            if discount_percentage < 0 or discount_percentage > 100:
                raise ValueError("Discount percentage must be between 0 and 100")
            self.discount_percentage = discount_percentage
            self.discount_amount = Decimal("0.00")
        
        if discount_amount is not None:
            if discount_amount < 0:
                raise ValueError("Discount amount cannot be negative")
            self.discount_amount = discount_amount
            self.discount_percentage = Decimal("0.00")
        
        self.calculate_line_total()
        self.updated_by = updated_by
    
    def process_return(
        self,
        return_quantity: Decimal,
        return_date: date,
        return_reason: Optional[str] = None,
        updated_by: Optional[str] = None
    ):
        """Process return for this line item."""
        if return_quantity <= 0:
            raise ValueError("Return quantity must be positive")
        
        if return_quantity > (self.quantity - self.returned_quantity):
            raise ValueError("Return quantity exceeds remaining quantity")
        
        self.returned_quantity += return_quantity
        self.return_date = return_date
        
        if return_reason:
            return_note = f"\n[RETURN] {return_date}: Qty {return_quantity} - {return_reason}"
            self.notes = (self.notes or "") + return_note
        
        self.updated_by = updated_by
    
    def update_rental_period(
        self,
        new_end_date: date,
        updated_by: Optional[str] = None
    ):
        """Update rental period end date."""
        if not self.rental_start_date:
            raise ValueError("Cannot update rental period for non-rental line")
        
        if new_end_date < self.rental_start_date:
            raise ValueError("End date must be after start date")
        
        self.rental_end_date = new_end_date
        
        # Recalculate rental days
        rental_days = (new_end_date - self.rental_start_date).days + 1
        
        # Update rental period value if using day units
        if self.rental_period_unit == RentalPeriodUnit.DAY.value:
            self.rental_period_value = rental_days
        
        self.updated_by = updated_by
    
    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate remaining quantity not yet returned."""
        return self.quantity - self.returned_quantity
    
    @property
    def is_fully_returned(self) -> bool:
        """Check if all items have been returned."""
        return self.returned_quantity >= self.quantity
    
    @property
    def is_partially_returned(self) -> bool:
        """Check if some items have been returned."""
        return 0 < self.returned_quantity < self.quantity
    
    @property
    def rental_days(self) -> int:
        """Calculate rental days."""
        if not self.rental_start_date or not self.rental_end_date:
            return 0
        return (self.rental_end_date - self.rental_start_date).days + 1
    
    @property
    def effective_unit_price(self) -> Decimal:
        """Calculate effective unit price after discount."""
        if self.quantity == 0:
            return Decimal("0.00")
        
        subtotal = self.quantity * self.unit_price
        discounted_amount = subtotal - self.discount_amount
        
        return discounted_amount / self.quantity
    
    @property
    def display_name(self) -> str:
        """Get line display name."""
        return f"Line {self.line_number}: {self.description}"
    
    def __str__(self) -> str:
        """String representation of transaction line."""
        return f"TransactionLine({self.line_number}: {self.description} - Qty: {self.quantity})"
    
    def __repr__(self) -> str:
        """Developer representation of transaction line."""
        return (
            f"TransactionLine(id={self.id}, line={self.line_number}, "
            f"type='{self.line_type}', qty={self.quantity}, "
            f"total=${self.line_total}, active={self.is_active})"
        )