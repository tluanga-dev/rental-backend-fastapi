"""
Rental lifecycle models for tracking rental operations and returns.
"""

from enum import Enum as PyEnum
from typing import Optional, List, TYPE_CHECKING
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy import Column, String, Numeric, Boolean, Text, DateTime, Date, ForeignKey, Integer, Index, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4

from app.db.base import BaseModel, UUIDType

if TYPE_CHECKING:
    from .transaction_headers import TransactionHeader
    from .transaction_lines import TransactionLine


class ReturnEventType(PyEnum):
    """Types of return events."""
    PARTIAL_RETURN = "PARTIAL_RETURN"
    FULL_RETURN = "FULL_RETURN"
    EXTENSION = "EXTENSION"
    STATUS_CHANGE = "STATUS_CHANGE"


class InspectionCondition(PyEnum):
    """Item condition after inspection."""
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"
    DAMAGED = "DAMAGED"


class RentalLifecycle(BaseModel):
    """
    Tracks the operational lifecycle of a rental transaction.
    
    This model separates rental operations from financial records,
    allowing for complex rental workflows while keeping transaction
    data clean and focused on financial aspects.
    """
    
    __tablename__ = "rental_lifecycles"
    
    # Primary identification
    id = Column(UUIDType(), primary_key=True, default=uuid4, comment="Unique lifecycle identifier")
    transaction_id = Column(UUIDType(), ForeignKey("transaction_headers.id"), nullable=False, unique=True, comment="Associated transaction")
    
    # Status tracking
    current_status = Column(String(30), nullable=False, comment="Current rental status")
    last_status_change = Column(DateTime, nullable=False, default=datetime.utcnow, comment="Last status change timestamp")
    status_changed_by = Column(UUIDType(), nullable=True, comment="User who changed status")
    
    # Return tracking
    total_returned_quantity = Column(Numeric(10, 2), nullable=False, default=0, comment="Total quantity returned across all events")
    expected_return_date = Column(Date, nullable=True, comment="Expected return date (may change with extensions)")
    
    # Fee accumulation
    total_late_fees = Column(Numeric(15, 2), nullable=False, default=0, comment="Accumulated late fees")
    total_damage_fees = Column(Numeric(15, 2), nullable=False, default=0, comment="Accumulated damage fees")
    total_other_fees = Column(Numeric(15, 2), nullable=False, default=0, comment="Other fees (cleaning, restocking, etc.)")
    
    # Notes and metadata
    notes = Column(Text, nullable=True, comment="General notes about the rental")
    
    # Relationships
    transaction = relationship("TransactionHeader", back_populates="rental_lifecycle", lazy="select")
    return_events = relationship("RentalReturnEvent", back_populates="rental_lifecycle", lazy="select", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_lifecycle_transaction", "transaction_id"),
        Index("idx_lifecycle_status", "current_status"),
        Index("idx_lifecycle_expected_return", "expected_return_date"),
    )
    
    def __repr__(self):
        return f"<RentalLifecycle(id={self.id}, transaction_id={self.transaction_id}, status={self.current_status})>"
    
    @property
    def total_fees(self):
        """Calculate total accumulated fees."""
        return self.total_late_fees + self.total_damage_fees + self.total_other_fees


class RentalReturnEvent(BaseModel):
    """
    Records individual return events during the rental lifecycle.
    
    A rental may have multiple return events:
    - Partial returns (some items returned)
    - Extensions (changing return date)
    - Final return (completing the rental)
    """
    
    __tablename__ = "rental_return_events"
    
    # Primary identification
    id = Column(UUIDType(), primary_key=True, default=uuid4, comment="Unique event identifier")
    rental_lifecycle_id = Column(UUIDType(), ForeignKey("rental_lifecycles.id"), nullable=False, comment="Associated rental lifecycle")
    
    # Event details
    event_type = Column(String(20), nullable=False, comment="Type of return event")
    event_date = Column(Date, nullable=False, comment="Date of the event")
    processed_by = Column(UUIDType(), nullable=True, comment="User who processed this event")
    processed_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="When the event was processed")
    
    # Return details (for return events)
    items_returned = Column(JSON, nullable=True, comment="JSON array of returned items with quantities and conditions")
    total_quantity_returned = Column(Numeric(10, 2), nullable=False, default=0, comment="Total quantity returned in this event")
    
    # Financial details
    late_fees_charged = Column(Numeric(15, 2), nullable=False, default=0, comment="Late fees charged in this event")
    damage_fees_charged = Column(Numeric(15, 2), nullable=False, default=0, comment="Damage fees charged in this event")
    other_fees_charged = Column(Numeric(15, 2), nullable=False, default=0, comment="Other fees charged in this event")
    payment_collected = Column(Numeric(15, 2), nullable=False, default=0, comment="Payment collected during this event")
    refund_issued = Column(Numeric(15, 2), nullable=False, default=0, comment="Refund issued during this event")
    
    # Extension details (for extension events)
    new_return_date = Column(Date, nullable=True, comment="New return date for extensions")
    extension_reason = Column(String(200), nullable=True, comment="Reason for extension")
    
    # Notes and documentation
    notes = Column(Text, nullable=True, comment="Notes about this event")
    receipt_number = Column(String(50), nullable=True, comment="Receipt number for payments/refunds")
    
    # Relationships
    rental_lifecycle = relationship("RentalLifecycle", back_populates="return_events", lazy="select")
    
    # Indexes
    __table_args__ = (
        Index("idx_return_event_lifecycle", "rental_lifecycle_id"),
        Index("idx_return_event_date", "event_date"),
        Index("idx_return_event_type", "event_type"),
        Index("idx_return_event_processed", "processed_at"),
    )
    
    def __repr__(self):
        return f"<RentalReturnEvent(id={self.id}, type={self.event_type}, date={self.event_date})>"
    
    @property
    def total_fees_charged(self):
        """Calculate total fees charged in this event."""
        return self.late_fees_charged + self.damage_fees_charged + self.other_fees_charged
    
    @property
    def net_amount(self):
        """Calculate net amount (payment collected minus refund issued)."""
        return self.payment_collected - self.refund_issued


class RentalItemInspection(BaseModel):
    """
    Records inspection details for individual items during returns.
    
    Each item returned gets inspected and its condition recorded.
    This enables per-item damage tracking and fee calculation.
    """
    
    __tablename__ = "rental_item_inspections"
    
    # Primary identification
    id = Column(UUIDType(), primary_key=True, default=uuid4, comment="Unique inspection identifier")
    return_event_id = Column(UUIDType(), ForeignKey("rental_return_events.id"), nullable=False, comment="Associated return event")
    transaction_line_id = Column(UUIDType(), ForeignKey("transaction_lines.id"), nullable=False, comment="Transaction line being inspected")
    
    # Inspection details
    quantity_inspected = Column(Numeric(10, 2), nullable=False, comment="Quantity of this item inspected")
    condition = Column(String(20), nullable=False, comment="Overall condition assessment")
    inspected_by = Column(UUIDType(), nullable=True, comment="User who performed inspection")
    inspected_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="Inspection timestamp")
    
    # Condition details
    has_damage = Column(Boolean, nullable=False, default=False, comment="Whether item has damage")
    damage_description = Column(Text, nullable=True, comment="Description of any damage")
    damage_photos = Column(JSON, nullable=True, comment="JSON array of damage photo URLs")
    
    # Financial impact
    damage_fee_assessed = Column(Numeric(15, 2), nullable=False, default=0, comment="Damage fee assessed for this item")
    cleaning_fee_assessed = Column(Numeric(15, 2), nullable=False, default=0, comment="Cleaning fee assessed for this item")
    replacement_required = Column(Boolean, nullable=False, default=False, comment="Whether item needs replacement")
    replacement_cost = Column(Numeric(15, 2), nullable=True, comment="Cost of replacement if required")
    
    # Stock handling
    return_to_stock = Column(Boolean, nullable=False, default=True, comment="Whether item can be returned to stock")
    stock_location = Column(String(100), nullable=True, comment="Where item was returned to stock")
    
    # Notes
    inspection_notes = Column(Text, nullable=True, comment="Detailed inspection notes")
    
    # Relationships
    return_event = relationship("RentalReturnEvent", lazy="select")
    transaction_line = relationship("TransactionLine", lazy="select")
    
    # Indexes
    __table_args__ = (
        Index("idx_inspection_return_event", "return_event_id"),
        Index("idx_inspection_transaction_line", "transaction_line_id"),
        Index("idx_inspection_condition", "condition"),
        Index("idx_inspection_damage", "has_damage"),
    )
    
    def __repr__(self):
        return f"<RentalItemInspection(id={self.id}, condition={self.condition}, quantity={self.quantity_inspected})>"
    
    @property
    def total_fees_assessed(self):
        """Calculate total fees assessed for this inspection."""
        return self.damage_fee_assessed + self.cleaning_fee_assessed + (self.replacement_cost or 0)


class RentalStatusChangeReason(PyEnum):
    """Reasons for rental status changes."""
    SCHEDULED_UPDATE = "SCHEDULED_UPDATE"
    RETURN_EVENT = "RETURN_EVENT"
    MANUAL_UPDATE = "MANUAL_UPDATE"
    EXTENSION = "EXTENSION"
    LATE_FEE_APPLIED = "LATE_FEE_APPLIED"
    DAMAGE_ASSESSMENT = "DAMAGE_ASSESSMENT"


class RentalStatusLog(BaseModel):
    """
    Historical log of rental status changes for both headers and line items.
    
    Tracks all status transitions with context about why they occurred,
    enabling comprehensive audit trails and status history reporting.
    """
    
    __tablename__ = "rental_status_logs"
    
    # Primary identification
    id = Column(UUIDType(), primary_key=True, default=uuid4, comment="Unique log entry identifier")
    
    # Entity identification
    transaction_id = Column(UUIDType(), ForeignKey("transaction_headers.id"), nullable=False, comment="Transaction being tracked")
    transaction_line_id = Column(UUIDType(), ForeignKey("transaction_lines.id"), nullable=True, comment="Specific line item (null for header-level changes)")
    rental_lifecycle_id = Column(UUIDType(), ForeignKey("rental_lifecycles.id"), nullable=True, comment="Associated rental lifecycle")
    
    # Status change details
    old_status = Column(String(30), nullable=True, comment="Previous status (null for initial status)")
    new_status = Column(String(30), nullable=False, comment="New status after change")
    change_reason = Column(String(30), nullable=False, comment="Reason for the status change")
    change_trigger = Column(String(50), nullable=True, comment="What triggered the change (scheduled_job, return_event_id, etc.)")
    
    # Change context
    changed_by = Column(UUIDType(), nullable=True, comment="User who initiated the change (null for system changes)")
    changed_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="When the change occurred")
    
    # Additional context
    notes = Column(Text, nullable=True, comment="Additional notes about the status change")
    status_metadata = Column(JSON, nullable=True, comment="Additional context data (overdue days, return quantities, etc.)")
    
    # System tracking
    system_generated = Column(Boolean, nullable=False, default=False, comment="Whether this change was system-generated")
    batch_id = Column(String(50), nullable=True, comment="Batch ID for scheduled updates")
    
    # Relationships
    transaction = relationship("TransactionHeader", lazy="select")
    transaction_line = relationship("TransactionLine", lazy="select")
    rental_lifecycle = relationship("RentalLifecycle", lazy="select")
    
    # Indexes
    __table_args__ = (
        Index("idx_status_log_transaction", "transaction_id"),
        Index("idx_status_log_line", "transaction_line_id"),
        Index("idx_status_log_changed_at", "changed_at"),
        Index("idx_status_log_reason", "change_reason"),
        Index("idx_status_log_batch", "batch_id"),
        Index("idx_status_log_system", "system_generated"),
    )
    
    def __repr__(self):
        entity_type = "line" if self.transaction_line_id else "header"
        return f"<RentalStatusLog(id={self.id}, {entity_type}, {self.old_status}->{self.new_status})>"
    
    @property
    def is_header_change(self) -> bool:
        """Check if this is a header-level status change."""
        return self.transaction_line_id is None
    
    @property
    def is_line_change(self) -> bool:
        """Check if this is a line-level status change."""
        return self.transaction_line_id is not None