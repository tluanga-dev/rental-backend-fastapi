"""
Transaction Line models - individual line items within transactions.
"""

from enum import Enum as PyEnum
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy import Column, String, Text, Numeric, DateTime, Date, Boolean, Integer, ForeignKey, Enum, Index, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.db.base import BaseModel, UUIDType

if TYPE_CHECKING:
    from .transaction_headers import TransactionHeader

# Import enums directly to avoid circular imports
from .transaction_headers import RentalPeriodUnit, RentalStatus


# Line Item Type Enum
class LineItemType(PyEnum):
    PRODUCT = "PRODUCT"
    SERVICE = "SERVICE"
    DISCOUNT = "DISCOUNT"
    TAX = "TAX"
    SHIPPING = "SHIPPING"
    FEE = "FEE"


class TransactionLine(BaseModel):
    """
    Transaction Line Item model for detailed transaction components.
    
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
        Index("idx_rental_status", "current_rental_status"),
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
    
    @property
    def return_percentage(self):
        """Calculate percentage of quantity returned."""
        if self.quantity == 0:
            return Decimal('0')
        return (self.returned_quantity / self.quantity) * 100
    
    @property
    def is_fully_returned(self):
        """Check if all quantity has been returned."""
        return self.returned_quantity >= self.quantity
    
    @property
    def is_partially_returned(self):
        """Check if some but not all quantity has been returned."""
        return 0 < self.returned_quantity < self.quantity
    
    @property
    def rental_duration_days(self):
        """Calculate rental duration in days for this line."""
        if self.rental_start_date and self.rental_end_date:
            return (self.rental_end_date - self.rental_start_date).days
        return 0
    
    @property
    def is_rental_overdue(self):
        """Check if this rental line is overdue."""
        if not self.rental_end_date:
            return False
        return self.rental_end_date < date.today() and not self.is_fully_returned
    
    @property
    def days_overdue(self):
        """Calculate days overdue for this rental line."""
        if not self.is_rental_overdue:
            return 0
        return (date.today() - self.rental_end_date).days
    
    @property
    def is_active_rental(self):
        """Check if this line represents an active rental."""
        return (self.current_rental_status == RentalStatus.ACTIVE and 
                self.rental_start_date and self.rental_end_date)
    
    @property
    def is_completed_rental(self):
        """Check if this rental line is completed."""
        return self.current_rental_status == RentalStatus.COMPLETED
    
    @property
    def is_late_rental(self):
        """Check if this rental line is late."""
        return (self.current_rental_status == RentalStatus.LATE or 
                self.current_rental_status == RentalStatus.LATE_PARTIAL_RETURN)
    
    @property
    def has_partial_return(self):
        """Check if this rental line has partial returns."""
        return (self.current_rental_status == RentalStatus.PARTIAL_RETURN or 
                self.current_rental_status == RentalStatus.LATE_PARTIAL_RETURN)
    
    def calculate_line_total(self):
        """Calculate and update line total."""
        extended = self.quantity * self.unit_price
        after_discount = extended - self.discount_amount
        self.line_total = after_discount + self.tax_amount
        return self.line_total
    
    def can_return_quantity(self, quantity: Decimal) -> bool:
        """Check if specified quantity can be returned."""
        return quantity <= self.remaining_quantity
    
    def calculate_daily_rate(self) -> Decimal:
        """Calculate daily rental rate for this line."""
        if self.daily_rate:
            return self.daily_rate
        
        if self.rental_duration_days > 0:
            return self.line_total / self.rental_duration_days
        
        return Decimal('0')