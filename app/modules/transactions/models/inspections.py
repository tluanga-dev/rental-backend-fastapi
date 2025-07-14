"""
Models for rental return inspections and purchase credit memos.
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, Numeric, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime

from app.db.base import BaseModel
from app.shared.utils.types import UUIDType


class RentalInspection(BaseModel):
    """Rental return inspection results."""
    
    __tablename__ = "rental_inspections"
    
    id = Column(UUIDType(), primary_key=True, default=uuid4)
    return_id = Column(UUIDType(), ForeignKey("transaction_headers.id"), nullable=False)
    inspector_id = Column(UUIDType(), ForeignKey("users.id"), nullable=False)
    inspection_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Overall assessment
    overall_condition = Column(String(20), nullable=False)  # EXCELLENT, GOOD, FAIR, POOR
    inspection_passed = Column(Boolean, nullable=False)
    
    # Financial calculations
    total_repair_cost = Column(Numeric(10, 2), nullable=False, default=0)
    total_cleaning_cost = Column(Numeric(10, 2), nullable=False, default=0)
    total_deductions = Column(Numeric(10, 2), nullable=False, default=0)
    deposit_refund_amount = Column(Numeric(10, 2), nullable=False, default=0)
    
    # Additional information
    general_notes = Column(Text)
    customer_notification_required = Column(Boolean, nullable=False, default=False)
    follow_up_actions = Column(JSON)  # List of follow-up actions
    
    # Line item inspections stored as JSON for flexibility
    line_inspections = Column(JSON, nullable=False)
    
    # Relationships
    return_transaction = relationship("TransactionHeader", foreign_keys=[return_id])
    inspector = relationship("User", foreign_keys=[inspector_id])


class PurchaseCreditMemo(BaseModel):
    """Purchase return credit memo tracking."""
    
    __tablename__ = "purchase_credit_memos"
    
    id = Column(UUIDType(), primary_key=True, default=uuid4)
    return_id = Column(UUIDType(), ForeignKey("transaction_headers.id"), nullable=False)
    credit_memo_number = Column(String(100), nullable=False, unique=True)
    credit_date = Column(DateTime, nullable=False)
    credit_amount = Column(Numeric(10, 2), nullable=False)
    
    # Credit details
    credit_type = Column(String(20), nullable=False)  # FULL_REFUND, PARTIAL_REFUND, etc.
    currency = Column(String(3), nullable=False, default="USD")
    exchange_rate = Column(Numeric(10, 6), nullable=False, default=1.0)
    
    # Line item breakdown (optional)
    line_credits = Column(JSON)
    
    # Additional information
    credit_terms = Column(String(500))
    supplier_notes = Column(Text)
    received_by = Column(UUIDType(), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    return_transaction = relationship("TransactionHeader", foreign_keys=[return_id])
    received_by_user = relationship("User", foreign_keys=[received_by])