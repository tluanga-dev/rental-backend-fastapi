"""
Purchase Models

Purchase-specific models that extend the base transaction models.
"""

from typing import TYPE_CHECKING
from sqlalchemy import Column, String, Numeric, Boolean, Text, Date, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.modules.transactions.base.models import TransactionHeader, TransactionLine, TransactionType

if TYPE_CHECKING:
    pass


class Purchase(TransactionHeader):
    """
    Purchase model extending TransactionHeader for purchase-specific functionality.
    
    This model uses table inheritance to add purchase-specific fields while
    maintaining the base transaction structure.
    """
    
    __tablename__ = "purchases"
    
    # Inherit from TransactionHeader
    id = Column(ForeignKey("transaction_headers.id"), primary_key=True)
    
    # Purchase-specific fields
    purchase_order_number = Column(String(50), unique=True, nullable=True, comment="Purchase order number")
    supplier_invoice_number = Column(String(50), nullable=True, comment="Supplier's invoice number")
    supplier_id = Column(String(36), nullable=True, comment="Supplier UUID as string")
    
    # Receiving tracking
    expected_date = Column(Date, nullable=True, comment="Expected delivery date")
    received_date = Column(Date, nullable=True, comment="Date when order was received")
    
    # Purchase terms
    payment_terms = Column(String(50), nullable=True, comment="Payment terms (e.g., Net 30)")
    freight_terms = Column(String(50), nullable=True, comment="Freight terms (e.g., FOB)")
    
    # Approval workflow
    approval_status = Column(String(20), nullable=False, default="PENDING", comment="Approval status")
    approved_by = Column(String(36), nullable=True, comment="User who approved the purchase")
    approved_date = Column(Date, nullable=True, comment="Date when purchase was approved")
    
    # Configure polymorphic identity
    __mapper_args__ = {
        "polymorphic_identity": TransactionType.PURCHASE,
        "inherit_condition": (id == TransactionHeader.id),
    }
    
    def __repr__(self):
        return f"<Purchase(id={self.id}, po_number={self.purchase_order_number}, supplier_id={self.supplier_id})>"


class PurchaseLine(TransactionLine):
    """
    Purchase line model extending TransactionLine for purchase-specific functionality.
    """
    
    __tablename__ = "purchase_lines"
    
    # Inherit from TransactionLine
    id = Column(ForeignKey("transaction_lines.id"), primary_key=True)
    
    # Purchase-specific fields
    supplier_item_code = Column(String(100), nullable=True, comment="Supplier's item code")
    received_quantity = Column(Numeric(10, 2), nullable=False, default=0, comment="Quantity received")
    pending_quantity = Column(Numeric(10, 2), nullable=False, default=0, comment="Quantity pending receipt")
    
    # Quality control
    inspection_required = Column(Boolean, nullable=False, default=False, comment="Whether inspection is required")
    # inspection_status is inherited from TransactionLine base model
    quality_rating = Column(String(1), nullable=True, comment="Quality rating (A-F)")
    
    # Configure polymorphic identity
    __mapper_args__ = {
        "polymorphic_identity": "PURCHASE_LINE",
        "inherit_condition": (id == TransactionLine.id),
    }
    
    def __repr__(self):
        return f"<PurchaseLine(id={self.id}, purchase_id={self.transaction_id}, description={self.description})>"
    
    @property
    def remaining_to_receive(self):
        """Calculate remaining quantity to receive."""
        return self.quantity - self.received_quantity
    
    @property
    def is_fully_received(self):
        """Check if all quantity has been received."""
        return self.received_quantity >= self.quantity
    
    @property
    def is_partially_received(self):
        """Check if some but not all quantity has been received."""
        return 0 < self.received_quantity < self.quantity
    
    @property
    def is_pending_receipt(self):
        """Check if item is pending receipt."""
        return self.pending_quantity > 0