"""
Dependencies for purchase transaction operations.
"""

from typing import Annotated

from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_session
from app.modules.transactions.purchase.service import PurchaseService


async def get_purchase_service(
    session: Annotated[AsyncSession, Depends(get_session)]
) -> PurchaseService:
    """Get purchase service instance."""
    return PurchaseService(session)
