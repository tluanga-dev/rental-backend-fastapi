"""
Base Transaction Models

Shared models and enums used by all transaction types.
"""

from enum import Enum as PyEnum
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
from datetime import datetime, date, time
from sqlalchemy import Column, String, Numeric, Boolean, Text, DateTime, Date, Time, ForeignKey, Integer, Index, Enum, CheckConstraint
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.db.base import BaseModel, UUIDType

if TYPE_CHECKING:
    # Temporarily commented out to avoid conflicts with legacy models
    # from app.modules.transactions.models.rental_lifecycle import RentalLifecycle
    # from app.modules.transactions.models.metadata import TransactionMetadata
    pass


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


# Line Item Type Enum
class LineItemType(PyEnum):
    PRODUCT = "PRODUCT"
    SERVICE = "SERVICE"
    DISCOUNT = "DISCOUNT"
    TAX = "TAX"
    SHIPPING = "SHIPPING"
    FEE = "FEE"


class TransactionHeader(BaseModel):
    """
    Base Transaction Header model for managing sales, purchases, and rentals.
    
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
    deposit_amount = Column(Numeric(15, 2), nullable=True, comment="Security deposit for rentals")
    deposit_paid = Column(Boolean, nullable=False, default=False, comment="Whether deposit has been paid")
    customer_advance_balance = Column(Numeric(15, 2), nullable=False, default=0, comment="Customer advance payment balance")
    
    # Return handling
    reference_transaction_id = Column(UUIDType(), ForeignKey("transaction_headers.id"), nullable=True, comment="Reference to original transaction for returns")
    
    # Additional information
    notes = Column(Text, nullable=True, comment="Additional notes")
    payment_method = Column(String(20), nullable=True, comment="Payment method")
    payment_reference = Column(String(100), nullable=True, comment="Payment reference")
    return_workflow_state = Column(String(50), nullable=True, comment="Return workflow state")
    
    # Delivery fields
    delivery_required = Column(Boolean, nullable=False, default=False, comment="Whether delivery is required")
    delivery_address = Column(Text, nullable=True, comment="Delivery address if delivery is required")
    delivery_date = Column(Date, nullable=True, comment="Scheduled delivery date")
    delivery_time = Column(Time, nullable=True, comment="Scheduled delivery time")
    
    # Pickup fields
    pickup_required = Column(Boolean, nullable=False, default=False, comment="Whether pickup is required")
    pickup_date = Column(Date, nullable=True, comment="Scheduled pickup date")
    pickup_time = Column(Time, nullable=True, comment="Scheduled pickup time")
    
    # Relationships
    reference_transaction = relationship("TransactionHeader", remote_side="TransactionHeader.id", lazy="select")
    transaction_lines = relationship("TransactionLine", back_populates="transaction", lazy="select", cascade="all, delete-orphan")
    # Temporarily commented out to avoid conflicts with legacy models
    # metadata_entries = relationship("TransactionMetadata", back_populates="transaction", lazy="select", cascade="all, delete-orphan")
    # rental_lifecycle = relationship("RentalLifecycle", back_populates="transaction", uselist=False, lazy="select")
    # Temporarily commented out to avoid conflicts with legacy models
    # events = relationship("TransactionEvent", back_populates="transaction", lazy="select", cascade="all, delete-orphan")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index("idx_transaction_number", "transaction_number"),
        Index("idx_transaction_type", "transaction_type"),
        Index("idx_transaction_status", "status"),
        Index("idx_transaction_date", "transaction_date"),
        Index("idx_customer_id", "customer_id"),
        Index("idx_location_id", "location_id"),
        Index("idx_reference_transaction", "reference_transaction_id"),
        Index("idx_delivery_required", "delivery_required"),
        Index("idx_pickup_required", "pickup_required"),
        Index("idx_delivery_date", "delivery_date"),
        Index("idx_pickup_date", "pickup_date"),
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
    def is_sale(self):
        """Check if this is a sale transaction."""
        return self.transaction_type == TransactionType.SALE
    
    @property
    def is_purchase(self):
        """Check if this is a purchase transaction."""
        return self.transaction_type == TransactionType.PURCHASE
    
    @property
    def is_return(self):
        """Check if this is a return transaction."""
        return self.transaction_type == TransactionType.RETURN


class TransactionLine(BaseModel):
    """
    Base Transaction Line Item model for detailed transaction components.
    
    Each line represents a specific item, service, or fee within a transaction.
    For rentals, tracks item-specific rental periods and return status.
    """
    
    __tablename__ = "transaction_lines"
    
    # Primary identification
    id = Column(UUIDType(), primary_key=True, default=uuid4, comment="Unique line item identifier")
    transaction_id = Column(UUIDType(), ForeignKey("transaction_headers.id"), nullable=False, comment="Parent transaction ID")
    line_number = Column(Integer, nullable=False, comment="Line sequence number within transaction")
    
    # Item identification
    line_type = Column(Enum(LineItemType), nullable=False, default=LineItemType.PRODUCT, comment="Type of line item")
    item_id = Column(String(36), nullable=True, comment="Item/Product UUID as string")
    inventory_unit_id = Column(String(36), nullable=True, comment="Specific inventory unit for serialized items")
    sku = Column(String(100), nullable=True, comment="Stock Keeping Unit")
    
    # Description and categorization
    description = Column(Text, nullable=False, comment="Line item description")
    category = Column(String(100), nullable=True, comment="Item category")
    
    # Quantity and measurements
    quantity = Column(Numeric(10, 2), nullable=False, default=1, comment="Quantity ordered/sold")
    unit_of_measure = Column(String(20), nullable=True, comment="Unit of measurement")
    
    # Pricing information
    unit_price = Column(Numeric(10, 2), nullable=False, default=0, comment="Price per unit")
    discount_percent = Column(Numeric(5, 2), nullable=False, default=0, comment="Discount percentage")
    discount_amount = Column(Numeric(10, 2), nullable=False, default=0, comment="Discount amount")
    tax_rate = Column(Numeric(5, 2), nullable=False, default=0, comment="Tax rate percentage")
    tax_amount = Column(Numeric(10, 2), nullable=False, default=0, comment="Tax amount")
    line_total = Column(Numeric(10, 2), nullable=False, default=0, comment="Total for this line item")
    
    # Rental-specific fields
    rental_start_date = Column(Date, nullable=True, comment="Item rental start date")
    rental_end_date = Column(Date, nullable=True, comment="Item rental end date")
    rental_period = Column(Integer, nullable=True, comment="Rental period for this item")
    rental_period_unit = Column(Enum(RentalPeriodUnit), nullable=True, comment="Rental period unit")
    current_rental_status = Column(Enum(RentalStatus), nullable=True, comment="Current rental status for this item")
    daily_rate = Column(Numeric(10, 2), nullable=True, comment="Daily rental rate")
    
    # Inventory and fulfillment
    location_id = Column(String(36), nullable=True, comment="Fulfillment location UUID as string")
    warehouse_location = Column(String(100), nullable=True, comment="Specific warehouse location")
    
    # Status tracking
    status = Column(String(20), nullable=False, default="PENDING", comment="Line item status")
    fulfillment_status = Column(String(20), nullable=False, default="PENDING", comment="Fulfillment status")
    
    # Return handling
    returned_quantity = Column(Numeric(10, 2), nullable=False, default=0, comment="Returned quantity")
    return_date = Column(Date, nullable=True, comment="Return date")
    notes = Column(Text, nullable=True, comment="Additional notes")
    return_condition = Column(String(1), nullable=True, default="A", comment="Return condition (A-D)")
    return_to_stock = Column(Boolean, nullable=True, default=True, comment="Whether to return to stock")
    inspection_status = Column(String(20), nullable=True, comment="Inspection status for returns")
    
    # Relationships
    transaction = relationship("TransactionHeader", back_populates="transaction_lines", lazy="select")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_transaction_id", "transaction_id"),
        Index("idx_line_number", "transaction_id", "line_number"),
        Index("idx_item_id", "item_id"),
        Index("idx_inventory_unit_id", "inventory_unit_id"),
        Index("idx_sku", "sku"),
        Index("idx_status", "status"),
        Index("idx_fulfillment_status", "fulfillment_status"),
        Index("idx_rental_dates", "rental_start_date", "rental_end_date"),
        Index("idx_rental_status", "current_rental_status"),
        CheckConstraint("quantity > 0", name="check_positive_quantity"),
        CheckConstraint("unit_price >= 0", name="check_non_negative_price"),
        CheckConstraint("discount_percent >= 0 AND discount_percent <= 100", name="check_valid_discount_percent"),
        CheckConstraint("tax_rate >= 0", name="check_non_negative_tax_rate"),
        CheckConstraint("returned_quantity >= 0", name="check_non_negative_returned"),
        CheckConstraint("returned_quantity <= quantity", name="check_returned_not_exceed_quantity"),
    )
    
    def __repr__(self):
        return f"<TransactionLine(id={self.id}, transaction_id={self.transaction_id}, line={self.line_number}, item={self.description})>"
    
    @property
    def extended_price(self):
        """Calculate extended price before discount."""
        return self.quantity * self.unit_price
    
    @property
    def net_amount(self):
        """Calculate net amount after discount but before tax."""
        return self.extended_price - self.discount_amount
    
    @property
    def remaining_quantity(self):
        """Calculate quantity not yet returned."""
        return self.quantity - self.returned_quantity
    
    @property
    def is_fully_returned(self):
        """Check if all quantity has been returned."""
        return self.returned_quantity >= self.quantity
    
    @property
    def is_partially_returned(self):
        """Check if some but not all quantity has been returned."""
        return 0 < self.returned_quantity < self.quantity