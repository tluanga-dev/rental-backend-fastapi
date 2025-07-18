"""
Sales Module

This module handles all sales-related operations including customer sales,
invoicing, and sales returns.
"""

from app.modules.sales.services import SalesService
from app.modules.sales.repository import SalesRepository
from app.modules.sales.schemas import (
    SaleCreate,
    SaleResponse,
    SaleUpdate,
    SaleInvoiceResponse,
    SaleListResponse,
)

__all__ = [
    "SalesService",
    "SalesRepository", 
    "SaleCreate",
    "SaleResponse",
    "SaleUpdate",
    "SaleInvoiceResponse",
    "SaleListResponse",
]