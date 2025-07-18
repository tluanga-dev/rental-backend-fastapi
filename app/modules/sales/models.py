"""
Sales Models

Sales-specific models that extend the base transaction models.
"""

from typing import TYPE_CHECKING
from sqlalchemy import Column, String, Numeric, Boolean, Text, Date, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.modules.transactions.base.models import TransactionHeader, TransactionLine, TransactionType

if TYPE_CHECKING:
    pass


class Sale(TransactionHeader):
    """
    Sale model extending TransactionHeader for sales-specific functionality.
    
    This model uses table inheritance to add sales-specific fields while
    maintaining the base transaction structure.
    """
    
    __tablename__ = "sales"
    
    # Inherit from TransactionHeader
    id = Column(ForeignKey("transaction_headers.id"), primary_key=True)
    
    # Sales-specific fields
    invoice_number = Column(String(50), unique=True, nullable=True, comment="Invoice number for this sale")
    customer_po_number = Column(String(50), nullable=True, comment="Customer purchase order number")
    sales_rep_commission = Column(Numeric(5, 2), nullable=True, comment="Sales rep commission percentage")
    customer_discount_percent = Column(Numeric(5, 2), nullable=True, comment="Customer-specific discount percentage")
    
    # Delivery tracking
    shipped_date = Column(Date, nullable=True, comment="Date when order was shipped")
    tracking_number = Column(String(100), nullable=True, comment="Shipping tracking number")
    carrier = Column(String(50), nullable=True, comment="Shipping carrier")
    
    # Customer service
    warranty_period_days = Column(Integer, nullable=True, comment="Warranty period in days")
    
    # Configure polymorphic identity
    __mapper_args__ = {
        "polymorphic_identity": TransactionType.SALE,
        "inherit_condition": (id == TransactionHeader.id),
    }
    
    def __repr__(self):
        return f"<Sale(id={self.id}, invoice_number={self.invoice_number}, customer_id={self.customer_id})>"


class SaleLine(TransactionLine):
    """
    Sale line model extending TransactionLine for sales-specific functionality.
    """
    
    __tablename__ = "sale_lines"
    
    # Inherit from TransactionLine
    id = Column(ForeignKey("transaction_lines.id"), primary_key=True)
    
    # Sales-specific fields
    customer_item_code = Column(String(100), nullable=True, comment="Customer's item code")
    shipped_quantity = Column(Numeric(10, 2), nullable=False, default=0, comment="Quantity shipped")
    backorder_quantity = Column(Numeric(10, 2), nullable=False, default=0, comment="Quantity on backorder")
    
    # Configure polymorphic identity
    __mapper_args__ = {
        "polymorphic_identity": "SALE_LINE",
        "inherit_condition": (id == TransactionLine.id),
    }
    
    def __repr__(self):
        return f"<SaleLine(id={self.id}, sale_id={self.transaction_id}, description={self.description})>"
    
    @property
    def remaining_to_ship(self):
        """Calculate remaining quantity to ship."""
        return self.quantity - self.shipped_quantity
    
    @property
    def is_fully_shipped(self):
        """Check if all quantity has been shipped."""
        return self.shipped_quantity >= self.quantity
    
    @property
    def is_backordered(self):
        """Check if item is on backorder."""
        return self.backorder_quantity > 0