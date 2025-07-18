"""
Sales Dependencies

Dependency injection for sales module.
"""

from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.modules.sales.services import SalesService
from app.modules.sales.repository import SalesRepository, SaleLineRepository


def get_sales_repository(
    session: AsyncSession = Depends(get_session)
) -> SalesRepository:
    """Get sales repository instance."""
    return SalesRepository(session)


def get_sale_line_repository(
    session: AsyncSession = Depends(get_session)
) -> SaleLineRepository:
    """Get sale line repository instance."""
    return SaleLineRepository(session)


def get_sales_service(
    session: AsyncSession = Depends(get_session)
) -> SalesService:
    """Get sales service instance."""
    return SalesService(session)


# Type aliases for dependency injection
SalesServiceDep = Annotated[SalesService, Depends(get_sales_service)]
SalesRepositoryDep = Annotated[SalesRepository, Depends(get_sales_repository)]
SaleLineRepositoryDep = Annotated[SaleLineRepository, Depends(get_sale_line_repository)]