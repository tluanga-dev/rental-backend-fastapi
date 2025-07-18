"""
Rental Models

Rental-specific models that extend the base transaction models.
"""

from typing import TYPE_CHECKING
from sqlalchemy import Column, String, Numeric, Boolean, Text, Date, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import BaseModel
from app.modules.transactions.base.models import TransactionHeader, TransactionLine, TransactionType, RentalStatus, RentalPeriodUnit

if TYPE_CHECKING:
    pass


class Rental(TransactionHeader):
    """
    Rental model extending TransactionHeader for rental-specific functionality.
    
    This model uses table inheritance to add rental-specific fields while
    maintaining the base transaction structure.
    """
    
    __tablename__ = "rentals"
    
    # Inherit from TransactionHeader
    id = Column(ForeignKey("transaction_headers.id"), primary_key=True)
    
    # Rental-specific fields
    rental_agreement_number = Column(String(50), unique=True, nullable=True, comment="Rental agreement number")
    rental_start_date = Column(Date, nullable=True, comment="Rental start date")
    rental_end_date = Column(Date, nullable=True, comment="Rental end date")
    actual_return_date = Column(Date, nullable=True, comment="Actual return date")
    
    # Rental terms
    rental_period = Column(Integer, nullable=True, comment="Rental period")
    rental_period_unit = Column(String(20), nullable=True, comment="Rental period unit")
    daily_rate = Column(Numeric(10, 2), nullable=True, comment="Daily rental rate")
    
    # Security deposit
    security_deposit_amount = Column(Numeric(15, 2), nullable=True, comment="Security deposit amount")
    security_deposit_paid = Column(Boolean, nullable=False, default=False, comment="Security deposit paid")
    
    # Late fees
    late_fee_rate = Column(Numeric(10, 2), nullable=True, comment="Late fee rate per day")
    late_fee_amount = Column(Numeric(15, 2), nullable=False, default=0, comment="Accumulated late fees")
    
    # Extension tracking
    extension_count = Column(Integer, nullable=False, default=0, comment="Number of extensions")
    max_extensions_allowed = Column(Integer, nullable=False, default=3, comment="Maximum extensions allowed")
    
    # Rental status
    rental_status = Column(String(30), nullable=False, default="ACTIVE", comment="Current rental status")
    
    # Configure polymorphic identity
    __mapper_args__ = {
        "polymorphic_identity": TransactionType.RENTAL,
        "inherit_condition": (id == TransactionHeader.id),
    }
    
    def __repr__(self):
        return f"<Rental(id={self.id}, agreement_number={self.rental_agreement_number}, customer_id={self.customer_id})>"
    
    @property
    def is_overdue(self):
        """Check if rental is overdue."""
        if not self.rental_end_date:
            return False
        return self.rental_end_date < datetime.now().date() and not self.actual_return_date
    
    @property
    def days_overdue(self):
        """Calculate days overdue."""
        if not self.is_overdue:
            return 0
        return (datetime.now().date() - self.rental_end_date).days
    
    @property
    def can_extend(self):
        """Check if rental can be extended."""
        return self.extension_count < self.max_extensions_allowed
    
    @property
    def is_completed(self):
        """Check if rental is completed."""
        return self.actual_return_date is not None


class RentalLine(TransactionLine):
    """
    Rental line model extending TransactionLine for rental-specific functionality.
    """
    
    __tablename__ = "rental_lines"
    
    # Inherit from TransactionLine
    id = Column(ForeignKey("transaction_lines.id"), primary_key=True)
    
    # Rental-specific fields
    item_serial_number = Column(String(100), nullable=True, comment="Serial number of rented item")
    item_condition_out = Column(String(1), nullable=True, default="A", comment="Item condition when rented out")
    item_condition_in = Column(String(1), nullable=True, comment="Item condition when returned")
    
    # Damage tracking
    damage_reported = Column(Boolean, nullable=False, default=False, comment="Damage reported")
    damage_description = Column(Text, nullable=True, comment="Damage description")
    damage_cost = Column(Numeric(10, 2), nullable=False, default=0, comment="Damage repair cost")
    
    # Late fees for individual items
    item_late_fee = Column(Numeric(10, 2), nullable=False, default=0, comment="Late fee for this item")
    
    # Configure polymorphic identity
    __mapper_args__ = {
        "polymorphic_identity": "RENTAL_LINE",
        "inherit_condition": (id == TransactionLine.id),
    }
    
    def __repr__(self):
        return f"<RentalLine(id={self.id}, rental_id={self.transaction_id}, description={self.description})>"
    
    @property
    def is_overdue(self):
        """Check if this rental line is overdue."""
        if not self.rental_end_date:
            return False
        return self.rental_end_date < datetime.now().date() and not self.return_date
    
    @property
    def days_overdue(self):
        """Calculate days overdue for this line."""
        if not self.is_overdue:
            return 0
        return (datetime.now().date() - self.rental_end_date).days
    
    @property
    def has_damage(self):
        """Check if item has damage."""
        return self.damage_reported or self.damage_cost > 0
    
    @property
    def total_cost(self):
        """Calculate total cost including damage and late fees."""
        return self.line_total + self.damage_cost + self.item_late_fee


class RentalLifecycle(BaseModel):
    """
    Rental lifecycle tracking model for operational aspects of rentals.
    """
    
    __tablename__ = "rental_lifecycles"
    
    # Primary identification
    id = Column(String(36), primary_key=True, comment="Unique lifecycle identifier")
    transaction_id = Column(ForeignKey("transaction_headers.id"), nullable=False, comment="Reference to rental transaction")
    
    # Lifecycle stages
    stage = Column(String(20), nullable=False, comment="Current lifecycle stage")
    stage_entered_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="When current stage was entered")
    
    # Operational fields
    checkout_completed = Column(Boolean, nullable=False, default=False, comment="Checkout completed")
    checkout_completed_at = Column(DateTime, nullable=True, comment="When checkout was completed")
    checkin_completed = Column(Boolean, nullable=False, default=False, comment="Check-in completed")
    checkin_completed_at = Column(DateTime, nullable=True, comment="When check-in was completed")
    
    # Inspection fields
    pre_rental_inspection = Column(Boolean, nullable=False, default=False, comment="Pre-rental inspection completed")
    post_rental_inspection = Column(Boolean, nullable=False, default=False, comment="Post-rental inspection completed")
    
    # Status tracking
    current_status = Column(String(30), nullable=False, default="ACTIVE", comment="Current rental status")
    
    # Relationships
    rental = relationship("TransactionHeader", back_populates="rental_lifecycle")
    
    def __repr__(self):
        return f"<RentalLifecycle(id={self.id}, transaction_id={self.transaction_id}, stage={self.stage})>"


class RentalExtension(BaseModel):
    """
    Rental extension tracking model.
    """
    
    __tablename__ = "rental_extensions"
    
    # Primary identification
    id = Column(String(36), primary_key=True, comment="Unique extension identifier")
    rental_id = Column(ForeignKey("transaction_headers.id"), nullable=False, comment="Reference to rental")
    
    # Extension details
    extension_number = Column(Integer, nullable=False, comment="Extension sequence number")
    original_end_date = Column(Date, nullable=False, comment="Original end date")
    new_end_date = Column(Date, nullable=False, comment="New end date")
    extension_days = Column(Integer, nullable=False, comment="Number of days extended")
    
    # Extension fee
    extension_fee = Column(Numeric(10, 2), nullable=False, default=0, comment="Extension fee charged")
    
    # Tracking
    requested_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="When extension was requested")
    approved_at = Column(DateTime, nullable=True, comment="When extension was approved")
    approved_by = Column(String(36), nullable=True, comment="Who approved the extension")
    
    # Reason
    reason = Column(Text, nullable=True, comment="Reason for extension")
    
    def __repr__(self):
        return f"<RentalExtension(id={self.id}, rental_id={self.rental_id}, extension_number={self.extension_number})>"