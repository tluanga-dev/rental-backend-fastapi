"""
Transaction routes for API endpoints.
"""

from fastapi import APIRouter

# Import purchase router
from app.modules.transactions.purchase.routes import router as purchase_router

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

# Include purchase routes without additional prefix since they're already prefixed
router.include_router(purchase_router, tags=["transactions"])