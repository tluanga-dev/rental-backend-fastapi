"""
Sales Module

Handles all sales-related transactions including creation, retrieval, and returns.
"""

from app.modules.transactions.sales.schemas import (
    SaleResponse,
    NewSaleRequest,
    NewSaleResponse,
    SaleItemCreate,
    SaleLineItemResponse,
    SaleDetail,
    SaleListResponse,
    CustomerNestedResponse,
    LocationNestedResponse,
    ItemNestedResponse,
)
from app.modules.transactions.sales.service import SalesService
from app.modules.transactions.sales.repository import SalesRepository
from app.modules.transactions.sales.routes import router as sales_router

__all__ = [
    # Schemas
    "SaleResponse",
    "NewSaleRequest",
    "NewSaleResponse",
    "SaleItemCreate",
    "SaleLineItemResponse",
    "SaleDetail",
    "SaleListResponse",
    "CustomerNestedResponse",
    "LocationNestedResponse",
    "ItemNestedResponse",
    # Service and Repository
    "SalesService",
    "SalesRepository",
    # Router
    "sales_router",
]