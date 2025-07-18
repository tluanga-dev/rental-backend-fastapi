"""
Dependencies for purchase transaction operations.
"""

from typing import Annotated

from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.modules.transactions.purchase.service import PurchaseService


async def get_purchase_service(
    session: Annotated[AsyncSession, Depends(get_db)]
) -> PurchaseService:
    """Get purchase service instance."""
    return PurchaseService(session)
