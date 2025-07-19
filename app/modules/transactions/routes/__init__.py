"""
Transaction routes package - Base router that combines all transaction sub-modules.
"""

from fastapi import APIRouter

# Import sub-module routers
from app.modules.transactions.purchase.routes import router as purchase_router
from app.modules.transactions.sales.routes import router as sales_router
from app.modules.transactions.rentals.routes import router as rentals_router
from app.modules.transactions.rental_returns.routes import router as rental_returns_router

# Import the cross-module query router
from .main import router as query_router

# Create base transaction router
router = APIRouter()

# Include sub-module routers with their prefixes
router.include_router(purchase_router, prefix="/purchases", tags=["Purchases"])
router.include_router(sales_router, prefix="/sales", tags=["Sales"])
router.include_router(rentals_router, prefix="/rentals", tags=["Rentals"])
router.include_router(rental_returns_router, prefix="/rental-returns", tags=["Rental Returns"])

# Include cross-module query endpoints (no prefix needed)
router.include_router(query_router, tags=["Transaction Queries"])

__all__ = ["router"]