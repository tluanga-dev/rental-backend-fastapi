"""
Transaction models package.
"""

# Import all models from the original models.py for backward compatibility
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, String, Text, Numeric, DateTime, Date, Boolean, Integer,
    ForeignKey, Enum, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime, date

from app.db.base import BaseModel, UUIDType


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


# Line Item Type Enum
class LineItemType(PyEnum):
    PRODUCT = "PRODUCT"
    SERVICE = "SERVICE"
    DISCOUNT = "DISCOUNT"
    TAX = "TAX"
    SHIPPING = "SHIPPING"
    FEE = "FEE"


class TransactionHeader(BaseModel):
    """Transaction Header model for managing sales, purchases, and rentals."""
    
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


class TransactionLine(BaseModel):
    """Transaction Line Item model for detailed transaction components."""
    
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
    # item = relationship("Item", back_populates="transaction_lines", lazy="select")  # Temporarily disabled
    # inventory_unit = relationship("InventoryUnit", back_populates="transaction_lines", lazy="select")  # Temporarily disabled
    # location = relationship("Location", back_populates="transaction_lines", lazy="select")  # Temporarily disabled
    
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
        UniqueConstraint("transaction_id", "line_number", name="uq_transaction_line_number"),
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
    
    def calculate_line_total(self):
        """Calculate and update line total."""
        extended = self.quantity * self.unit_price
        after_discount = extended - self.discount_amount
        self.line_total = after_discount + self.tax_amount
        return self.line_total


# Import metadata and inspection models
from .metadata import TransactionMetadata
from .inspections import RentalInspection, PurchaseCreditMemo

# Export all models
__all__ = [
    "TransactionType",
    "TransactionStatus", 
    "PaymentMethod",
    "PaymentStatus",
    "RentalPeriodUnit",
    "LineItemType",
    "TransactionHeader",
    "TransactionLine",
    "TransactionMetadata",
    "RentalInspection",
    "PurchaseCreditMemo"
]