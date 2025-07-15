"""
Transaction Header model - main transaction records.
"""

from enum import Enum as PyEnum
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy import Column, String, Numeric, Boolean, Text, DateTime, Date, ForeignKey, Integer, Index, Enum, CheckConstraint
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.db.base import BaseModel, UUIDType

if TYPE_CHECKING:
    from app.modules.transactions.models.lines import TransactionLine
    from app.modules.transactions.models.rental_lifecycle import RentalLifecycle
    from app.modules.rentals.models import RentalReturn
    from app.modules.transactions.models.metadata import TransactionMetadata


# Transaction Type Enum
class TransactionType(PyEnum):
    SALE = "SALE"
    PURCHASE = "PURCHASE"
    RENTAL = "RENTAL"
    RETURN = "RETURN"
    ADJUSTMENT = "ADJUSTMENT"


# Transaction Status Enum
class TransactionStatus(PyEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    ON_HOLD = "ON_HOLD"
    IN_PROGRESS = "IN_PROGRESS"  # For rentals


# Payment Method Enum
class PaymentMethod(PyEnum):
    CASH = "CASH"
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    BANK_TRANSFER = "BANK_TRANSFER"
    CHEQUE = "CHEQUE"
    ONLINE = "ONLINE"
    CREDIT_ACCOUNT = "CREDIT_ACCOUNT"


# Payment Status Enum
class PaymentStatus(PyEnum):
    PENDING = "PENDING"
    PAID = "PAID"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


# Rental Period Unit Enum
class RentalPeriodUnit(PyEnum):
    HOUR = "HOUR"
    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"


# Rental Status Enum
class RentalStatus(PyEnum):
    ACTIVE = "ACTIVE"
    LATE = "LATE"
    EXTENDED = "EXTENDED"
    PARTIAL_RETURN = "PARTIAL_RETURN"
    LATE_PARTIAL_RETURN = "LATE_PARTIAL_RETURN"
    COMPLETED = "COMPLETED"


class TransactionHeader(BaseModel):
    """
    Transaction Header model for managing sales, purchases, and rentals.
    
    This is the main financial record that tracks all monetary aspects of transactions.
    For rentals, it works with RentalLifecycle for operational tracking.
    """
    
    __tablename__ = "transaction_headers"
    
    # Primary identification
    id = Column(UUIDType(), primary_key=True, default=uuid4, comment="Unique transaction identifier")
    transaction_number = Column(String(50), unique=True, nullable=False, comment="Human-readable transaction number")
    
    # Transaction categorization
    transaction_type = Column(Enum(TransactionType), nullable=False, comment="Type of transaction")
    status = Column(Enum(TransactionStatus), nullable=False, default=TransactionStatus.PENDING, comment="Current status")
    
    # Temporal information
    transaction_date = Column(DateTime, nullable=False, default=datetime.utcnow, comment="Transaction date and time")
    due_date = Column(Date, nullable=True, comment="Payment due date")
    
    # Parties involved
    customer_id = Column(String(36), nullable=True, comment="Customer/Supplier UUID as string")
    location_id = Column(String(36), nullable=True, comment="Location UUID as string")
    sales_person_id = Column(UUIDType(), nullable=True, comment="Sales person handling transaction")
    
    # Financial information
    currency = Column(String(3), nullable=False, default="USD", comment="Currency code")
    exchange_rate = Column(Numeric(10, 6), nullable=False, default=1.0, comment="Exchange rate to base currency")
    
    # Amount calculations
    subtotal = Column(Numeric(15, 2), nullable=False, default=0, comment="Subtotal before discounts and taxes")
    discount_amount = Column(Numeric(15, 2), nullable=False, default=0, comment="Total discount amount")
    tax_amount = Column(Numeric(15, 2), nullable=False, default=0, comment="Total tax amount")
    shipping_amount = Column(Numeric(15, 2), nullable=False, default=0, comment="Shipping charges")
    total_amount = Column(Numeric(15, 2), nullable=False, default=0, comment="Final total amount")
    paid_amount = Column(Numeric(15, 2), nullable=False, default=0, comment="Amount already paid")
    
    # Rental-specific fields
    rental_start_date = Column(Date, nullable=True, comment="Rental start date")
    rental_end_date = Column(Date, nullable=True, comment="Rental end date")
    rental_period = Column(Integer, nullable=True, comment="Rental period duration")
    rental_period_unit = Column(Enum(RentalPeriodUnit), nullable=True, comment="Rental period unit")
    deposit_amount = Column(Numeric(15, 2), nullable=True, comment="Security deposit for rentals")
    deposit_paid = Column(Boolean, nullable=False, default=False, comment="Whether deposit has been paid")
    current_rental_status = Column(Enum(RentalStatus), nullable=True, comment="Current rental status")
    customer_advance_balance = Column(Numeric(15, 2), nullable=False, default=0, comment="Customer advance payment balance")
    
    # Return handling
    reference_transaction_id = Column(UUIDType(), ForeignKey("transaction_headers.id"), nullable=True, comment="Reference to original transaction for returns")
    
    # Additional information
    notes = Column(Text, nullable=True, comment="Additional notes")
    payment_method = Column(String(20), nullable=True, comment="Payment method")
    payment_reference = Column(String(100), nullable=True, comment="Payment reference")
    return_workflow_state = Column(String(50), nullable=True, comment="Return workflow state")
    
    # Relationships
    # customer = relationship("Customer", back_populates="transactions", lazy="select")  # Temporarily disabled
    # location = relationship("Location", back_populates="transactions", lazy="select")  # Temporarily disabled
    # sales_person = relationship("User", back_populates="transactions", lazy="select")  # Temporarily disabled
    reference_transaction = relationship("TransactionHeader", remote_side="TransactionHeader.id", lazy="select")
    transaction_lines = relationship("TransactionLine", back_populates="transaction", lazy="select", cascade="all, delete-orphan")
    rental_returns = relationship("RentalReturn", back_populates="rental_transaction", lazy="select")
    metadata_entries = relationship("TransactionMetadata", back_populates="transaction", lazy="select", cascade="all, delete-orphan")
    rental_lifecycle = relationship("RentalLifecycle", back_populates="transaction", uselist=False, lazy="select")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index("idx_transaction_number", "transaction_number"),
        Index("idx_transaction_type", "transaction_type"),
        Index("idx_transaction_status", "status"),
        Index("idx_transaction_date", "transaction_date"),
        Index("idx_customer_id", "customer_id"),
        Index("idx_location_id", "location_id"),
        Index("idx_reference_transaction", "reference_transaction_id"),
        Index("idx_rental_dates", "rental_start_date", "rental_end_date"),
        Index("idx_rental_status", "current_rental_status"),
        CheckConstraint("total_amount >= 0", name="check_positive_total"),
        CheckConstraint("paid_amount >= 0", name="check_positive_paid"),
        CheckConstraint("paid_amount <= total_amount", name="check_paid_not_exceed_total"),
    )
    
    def __repr__(self):
        return f"<TransactionHeader(id={self.id}, number={self.transaction_number}, type={self.transaction_type}, total={self.total_amount})>"
    
    @property
    def balance_due(self):
        """Calculate outstanding balance."""
        return self.total_amount - self.paid_amount
    
    @property
    def is_paid(self):
        """Check if transaction is fully paid."""
        return self.paid_amount >= self.total_amount
    
    @property
    def payment_status(self):
        """Determine payment status."""
        if self.paid_amount == 0:
            return PaymentStatus.PENDING
        elif self.paid_amount >= self.total_amount:
            return PaymentStatus.PAID
        else:
            return PaymentStatus.PARTIAL
    
    @property
    def is_rental(self):
        """Check if this is a rental transaction."""
        return self.transaction_type == TransactionType.RENTAL
    
    @property
    def rental_duration_days(self):
        """Calculate rental duration in days."""
        if self.rental_start_date and self.rental_end_date:
            return (self.rental_end_date - self.rental_start_date).days
        return 0
    
    @property
    def is_overdue(self):
        """Check if rental is overdue."""
        if not self.is_rental or not self.rental_end_date:
            return False
        return self.rental_end_date < date.today()
    
    @property
    def days_overdue(self):
        """Calculate days overdue for rental."""
        if not self.is_overdue:
            return 0
        return (date.today() - self.rental_end_date).days