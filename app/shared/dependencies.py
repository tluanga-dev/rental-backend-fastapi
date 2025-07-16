from typing import Optional, Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.db.session import get_session
from app.core.config import settings
# Database dependency
AsyncSessionDep = Annotated[AsyncSession, Depends(get_session)]


# Common query parameters
class CommonQueryParams(BaseModel):
    """Common query parameters for list endpoints."""
    
    skip: int = Query(0, ge=0, description="Number of records to skip")
    limit: int = Query(
        settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description="Number of records to return"
    )
    sort_by: Optional[str] = Query(None, description="Field to sort by")
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order")
    search: Optional[str] = Query(None, description="Search term")
    is_active: Optional[bool] = Query(None, description="Filter by active status")


class PaginationParams(BaseModel):
    """Pagination parameters."""
    
    page: int = Query(1, ge=1, description="Page number")
    page_size: int = Query(
        settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description="Items per page"
    )
    
    @property
    def skip(self) -> int:
        """Calculate skip value from page number."""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Get limit value."""
        return self.page_size


# Repository dependencies
# These will be implemented as modules are created


async def get_brand_repository(session: AsyncSessionDep):
    """Get brand repository instance."""
    from app.modules.master_data.brands.repository import BrandRepository
    return BrandRepository(session)


async def get_category_repository(session: AsyncSessionDep):
    """Get category repository instance."""
    from app.modules.master_data.categories.repository import CategoryRepository
    return CategoryRepository(session)


async def get_unit_repository(session: AsyncSessionDep):
    """Get unit repository instance."""
    from app.modules.master_data.units.repository import UnitRepository
    return UnitRepository(session)


async def get_unit_of_measurement_repository(session: AsyncSessionDep):
    """Get unit of measurement repository instance."""
    from app.modules.master_data.units.repository import UnitOfMeasurementRepository
    return UnitOfMeasurementRepository(session)


# Service dependencies


async def get_customer_service(
    session: AsyncSessionDep
):
    """Get customer service instance."""
    from app.modules.customers.service import CustomerService
    return CustomerService(session)


async def get_supplier_service(
    session: AsyncSessionDep
):
    """Get supplier service instance."""
    from app.modules.suppliers.service import SupplierService
    return SupplierService(session)


async def get_inventory_service(
    session: AsyncSessionDep
):
    """Get inventory service instance."""
    from app.modules.inventory.service import InventoryService
    return InventoryService(session)


async def get_transaction_service(
    session: AsyncSessionDep
):
    """Get transaction service instance."""
    from app.modules.transactions.service import TransactionService
    return TransactionService(session)


async def get_location_service(
    session: AsyncSessionDep
):
    """Get location service instance."""
    from app.modules.master_data.locations.service import LocationService
    return LocationService(session)




async def get_brand_service(
    brand_repo = Depends(get_brand_repository)
):
    """Get brand service instance."""
    from app.modules.master_data.brands.service import BrandService
    return BrandService(brand_repo)


async def get_category_service(
    category_repo = Depends(get_category_repository)
):
    """Get category service instance."""
    from app.modules.master_data.categories.service import CategoryService
    return CategoryService(category_repo)


async def get_unit_service(
    unit_repo = Depends(get_unit_repository)
):
    """Get unit service instance."""
    from app.modules.master_data.units.service import UnitService
    return UnitService(unit_repo)


async def get_unit_of_measurement_service(
    unit_repo = Depends(get_unit_of_measurement_repository)
):
    """Get unit of measurement service instance."""
    from app.modules.master_data.units.service import UnitOfMeasurementService
    return UnitOfMeasurementService(unit_repo)


async def get_rental_service(
    session: AsyncSessionDep
):
    """Get rental service instance."""
    from app.modules.rentals.service import RentalService
    return RentalService(session)


async def get_analytics_service(
    session: AsyncSessionDep
):
    """Get analytics service instance."""
    from app.modules.analytics.service import AnalyticsService
    return AnalyticsService(session)


async def get_system_service(
    session: AsyncSessionDep
):
    """Get system service instance."""
    from app.modules.system.service import SystemService
    return SystemService(session)






async def get_customer_repository(session: AsyncSessionDep):
    """Get customer repository instance."""
    from app.modules.customers.repository import CustomerRepository
    return CustomerRepository(session)


async def get_supplier_repository(session: AsyncSessionDep):
    """Get supplier repository instance."""
    from app.modules.suppliers.repository import SupplierRepository
    return SupplierRepository(session)


async def get_inventory_repository(session: AsyncSessionDep):
    """Get inventory repository instance."""
    from app.modules.inventory.repository import InventoryRepository
    return InventoryRepository(session)


async def get_transaction_repository(session: AsyncSessionDep):
    """Get transaction repository instance."""
    from app.modules.transactions.repository import TransactionRepository
    return TransactionRepository(session)


async def get_rental_repository(session: AsyncSessionDep):
    """Get rental repository instance."""
    from app.modules.rentals.repository import RentalRepository
    return RentalRepository(session)


async def get_location_repository(session: AsyncSessionDep):
    """Get location repository instance."""
    from app.modules.master_data.locations.repository import LocationRepository
    return LocationRepository(session)




# API Key dependency (for external integrations)
async def get_api_key(
    api_key: str = Query(..., description="API Key for authentication")
) -> str:
    """
    Validate API key from query parameter.
    """
    # TODO: Implement API key validation
    # This would check against stored API keys in database
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    # Temporary validation
    if api_key != "test-api-key":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return api_key


# Request ID dependency (for request tracking)
async def get_request_id() -> str:
    """
    Generate unique request ID for tracking.
    """
    import uuid
    return str(uuid.uuid4())


# Export commonly used dependencies
__all__ = [
    "AsyncSessionDep",
    "CommonQueryParams",
    "PaginationParams",
    "get_api_key",
    "get_request_id",
    "get_customer_service",
    "get_supplier_service",
    "get_inventory_service",
    "get_transaction_service",
    "get_rental_service",
    "get_analytics_service",
    "get_system_service",
    "get_brand_service",
    "get_category_service",
    "get_location_service",
    "get_unit_service",
    "get_unit_of_measurement_service",
]