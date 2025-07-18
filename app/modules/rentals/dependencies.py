"""
Rental Dependencies

Dependency injection for rentals module.
"""

from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.modules.rentals.services import RentalsService
from app.modules.rentals.repository import RentalsRepository, RentalLineRepository, RentalLifecycleRepository


def get_rentals_repository(
    session: AsyncSession = Depends(get_session)
) -> RentalsRepository:
    """Get rentals repository instance."""
    return RentalsRepository(session)


def get_rental_line_repository(
    session: AsyncSession = Depends(get_session)
) -> RentalLineRepository:
    """Get rental line repository instance."""
    return RentalLineRepository(session)


def get_rental_lifecycle_repository(
    session: AsyncSession = Depends(get_session)
) -> RentalLifecycleRepository:
    """Get rental lifecycle repository instance."""
    return RentalLifecycleRepository(session)


def get_rentals_service(
    session: AsyncSession = Depends(get_session)
) -> RentalsService:
    """Get rentals service instance."""
    return RentalsService(session)


# Type aliases for dependency injection
RentalsServiceDep = Annotated[RentalsService, Depends(get_rentals_service)]
RentalsRepositoryDep = Annotated[RentalsRepository, Depends(get_rentals_repository)]
RentalLineRepositoryDep = Annotated[RentalLineRepository, Depends(get_rental_line_repository)]
RentalLifecycleRepositoryDep = Annotated[RentalLifecycleRepository, Depends(get_rental_lifecycle_repository)]