"""
Rent Return Dependencies

Dependency injection for rent returns module.
"""

from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.modules.rent_returns.services import RentReturnsService
from app.modules.rent_returns.repository import RentReturnsRepository, RentReturnLineRepository, RentReturnInspectionRepository


def get_rent_returns_repository(
    session: AsyncSession = Depends(get_session)
) -> RentReturnsRepository:
    """Get rent returns repository instance."""
    return RentReturnsRepository(session)


def get_rent_return_line_repository(
    session: AsyncSession = Depends(get_session)
) -> RentReturnLineRepository:
    """Get rent return line repository instance."""
    return RentReturnLineRepository(session)


def get_rent_return_inspection_repository(
    session: AsyncSession = Depends(get_session)
) -> RentReturnInspectionRepository:
    """Get rent return inspection repository instance."""
    return RentReturnInspectionRepository(session)


def get_rent_returns_service(
    session: AsyncSession = Depends(get_session)
) -> RentReturnsService:
    """Get rent returns service instance."""
    return RentReturnsService(session)


# Type aliases for dependency injection
RentReturnsServiceDep = Annotated[RentReturnsService, Depends(get_rent_returns_service)]
RentReturnsRepositoryDep = Annotated[RentReturnsRepository, Depends(get_rent_returns_repository)]
RentReturnLineRepositoryDep = Annotated[RentReturnLineRepository, Depends(get_rent_return_line_repository)]
RentReturnInspectionRepositoryDep = Annotated[RentReturnInspectionRepository, Depends(get_rent_return_inspection_repository)]