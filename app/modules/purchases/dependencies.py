"""
Purchase Dependencies

Dependency injection for purchases module.
"""

from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.modules.purchases.services import PurchasesService
from app.modules.purchases.repository import PurchasesRepository, PurchaseLineRepository


def get_purchases_repository(
    session: AsyncSession = Depends(get_session)
) -> PurchasesRepository:
    """Get purchases repository instance."""
    return PurchasesRepository(session)


def get_purchase_line_repository(
    session: AsyncSession = Depends(get_session)
) -> PurchaseLineRepository:
    """Get purchase line repository instance."""
    return PurchaseLineRepository(session)


def get_purchases_service(
    session: AsyncSession = Depends(get_session)
) -> PurchasesService:
    """Get purchases service instance."""
    return PurchasesService(session)


# Type aliases for dependency injection
PurchasesServiceDep = Annotated[PurchasesService, Depends(get_purchases_service)]
PurchasesRepositoryDep = Annotated[PurchasesRepository, Depends(get_purchases_repository)]
PurchaseLineRepositoryDep = Annotated[PurchaseLineRepository, Depends(get_purchase_line_repository)]