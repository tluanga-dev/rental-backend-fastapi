"""
Rent Return Models

Return-specific models that extend the base transaction models.
"""

from typing import TYPE_CHECKING
from sqlalchemy import Column, String, Numeric, Boolean, Text, Date, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import BaseModel
from app.modules.transactions.base.models import TransactionHeader, TransactionLine, TransactionType

if TYPE_CHECKING:
    pass


class RentReturn(TransactionHeader):
    """
    Rent Return model extending TransactionHeader for return-specific functionality.
    
    This model uses table inheritance to add return-specific fields while
    maintaining the base transaction structure.
    """
    
    __tablename__ = "rent_returns"
    
    # Inherit from TransactionHeader
    id = Column(ForeignKey("transaction_headers.id"), primary_key=True)
    
    # Return-specific fields
    return_number = Column(String(50), unique=True, nullable=True, comment="Return number")
    original_rental_id = Column(ForeignKey("transaction_headers.id"), nullable=False, comment="Original rental transaction")
    
    # Return details
    return_date = Column(Date, nullable=False, comment="Date of return")
    return_reason = Column(String(100), nullable=True, comment="Reason for return")
    
    # Inspection details
    inspection_completed = Column(Boolean, nullable=False, default=False, comment="Inspection completed")
    inspection_date = Column(Date, nullable=True, comment="Date of inspection")
    inspected_by = Column(String(36), nullable=True, comment="Who performed the inspection")
    
    # Damage assessment
    total_damage_cost = Column(Numeric(15, 2), nullable=False, default=0, comment="Total damage cost")
    damage_deposit_deducted = Column(Numeric(15, 2), nullable=False, default=0, comment="Amount deducted from deposit")
    
    # Cleaning fees
    cleaning_required = Column(Boolean, nullable=False, default=False, comment="Cleaning required")
    cleaning_cost = Column(Numeric(10, 2), nullable=False, default=0, comment="Cleaning cost")
    
    # Late fees
    late_return = Column(Boolean, nullable=False, default=False, comment="Late return")
    late_fee_amount = Column(Numeric(10, 2), nullable=False, default=0, comment="Late fee amount")
    
    # Deposit refund
    deposit_refund_amount = Column(Numeric(15, 2), nullable=False, default=0, comment="Deposit refund amount")
    deposit_refund_processed = Column(Boolean, nullable=False, default=False, comment="Deposit refund processed")
    deposit_refund_date = Column(Date, nullable=True, comment="Date deposit was refunded")
    
    # Relationships
    original_rental = relationship("TransactionHeader", foreign_keys=[original_rental_id], lazy="select")
    
    # Configure polymorphic identity
    __mapper_args__ = {
        "polymorphic_identity": TransactionType.RETURN,
        "inherit_condition": (id == TransactionHeader.id),
    }
    
    def __repr__(self):
        return f"<RentReturn(id={self.id}, return_number={self.return_number}, original_rental_id={self.original_rental_id})>"
    
    @property
    def total_deductions(self):
        """Calculate total deductions from deposit."""
        return self.total_damage_cost + self.cleaning_cost + self.late_fee_amount
    
    @property
    def net_refund_amount(self):
        """Calculate net refund amount after deductions."""
        return max(0, self.deposit_refund_amount - self.total_deductions)
    
    @property
    def has_damage(self):
        """Check if return has damage."""
        return self.total_damage_cost > 0
    
    @property
    def requires_cleaning(self):
        """Check if return requires cleaning."""
        return self.cleaning_required or self.cleaning_cost > 0


class RentReturnLine(TransactionLine):
    """
    Rent Return line model extending TransactionLine for return-specific functionality.
    """
    
    __tablename__ = "rent_return_lines"
    
    # Inherit from TransactionLine
    id = Column(ForeignKey("transaction_lines.id"), primary_key=True)
    
    # Return-specific fields
    original_rental_line_id = Column(ForeignKey("transaction_lines.id"), nullable=False, comment="Original rental line")
    
    # Item condition
    condition_on_return = Column(String(1), nullable=False, default="A", comment="Item condition on return (A-F)")
    
    # Damage details
    damage_noted = Column(Boolean, nullable=False, default=False, comment="Damage noted")
    damage_description = Column(Text, nullable=True, comment="Detailed damage description")
    damage_photos = Column(Text, nullable=True, comment="URLs of damage photos")
    repair_cost = Column(Numeric(10, 2), nullable=False, default=0, comment="Estimated repair cost")
    
    # Cleaning details
    cleaning_notes = Column(Text, nullable=True, comment="Cleaning notes")
    cleaning_fee = Column(Numeric(10, 2), nullable=False, default=0, comment="Cleaning fee for this item")
    
    # Return processing
    return_to_inventory = Column(Boolean, nullable=False, default=True, comment="Return item to inventory")
    inventory_location = Column(String(100), nullable=True, comment="Inventory location")
    
    # Relationships
    original_rental_line = relationship("TransactionLine", foreign_keys=[original_rental_line_id], lazy="select")
    
    # Configure polymorphic identity
    __mapper_args__ = {
        "polymorphic_identity": "RENT_RETURN_LINE",
        "inherit_condition": (id == TransactionLine.id),
    }
    
    def __repr__(self):
        return f"<RentReturnLine(id={self.id}, return_id={self.transaction_id}, condition={self.condition_on_return})>"
    
    @property
    def total_fees(self):
        """Calculate total fees for this item."""
        return self.repair_cost + self.cleaning_fee
    
    @property
    def is_damaged(self):
        """Check if item is damaged."""
        return self.damage_noted or self.repair_cost > 0
    
    @property
    def needs_cleaning(self):
        """Check if item needs cleaning."""
        return self.cleaning_fee > 0


class RentReturnInspection(BaseModel):
    """
    Rent Return inspection model for detailed inspection records.
    """
    
    __tablename__ = "rent_return_inspections"
    
    # Primary identification
    id = Column(String(36), primary_key=True, comment="Unique inspection identifier")
    return_id = Column(ForeignKey("transaction_headers.id"), nullable=False, comment="Reference to return transaction")
    
    # Inspection details
    inspection_type = Column(String(20), nullable=False, comment="Type of inspection")
    inspection_date = Column(DateTime, nullable=False, default=datetime.utcnow, comment="Inspection date")
    inspector_id = Column(String(36), nullable=False, comment="Inspector user ID")
    
    # Inspection results
    overall_condition = Column(String(1), nullable=False, comment="Overall condition grade")
    inspection_notes = Column(Text, nullable=True, comment="Detailed inspection notes")
    
    # Damage assessment
    damage_items = Column(Text, nullable=True, comment="JSON list of damaged items")
    total_damage_value = Column(Numeric(15, 2), nullable=False, default=0, comment="Total damage value")
    
    # Photos and documentation
    photos = Column(Text, nullable=True, comment="URLs of inspection photos")
    documents = Column(Text, nullable=True, comment="URLs of related documents")
    
    # Approval
    approved = Column(Boolean, nullable=False, default=False, comment="Inspection approved")
    approved_by = Column(String(36), nullable=True, comment="Who approved the inspection")
    approved_date = Column(DateTime, nullable=True, comment="Approval date")
    
    def __repr__(self):
        return f"<RentReturnInspection(id={self.id}, return_id={self.return_id}, condition={self.overall_condition})>"